    // Validate actual SDK fusion metadata against every pinned original HardOp.
    // No legacy group IDs, Scatter callbacks or guessed completion thresholds.
    inline void validate_applied_bindings(const Session& session, const xir::Network& graph, const fs::path& output) {
        const auto ops = checked_originals(session, graph);
        const auto bindings = session.backendBindings();
        const auto& zg_backend = session->backends[0];
        const auto& host_backend = session->backends[1];
        const auto info = zg_backend.cast<zg330::ZG330Backend>()->forward_info;
        need(info.defined(), "Undefined ZG forward metadata");
        std::set<int64_t> hard, groups, deployed_host, expected_keys, map_keys, sync_keys;
        for (const auto& item : ops) if (item.second.is<xir::HardOp>()) hard.insert(item.first);
        std::map<int64_t,int64_t> effective;
        std::map<int,int64_t> ordered;
        pose_v1::fusion_baseline::members.clear();
        pose_v1::fusion_baseline::sync.clear();
        for (const auto& item : bindings) {
            if (item.second.same_as(host_backend)) {
                need(pose_v1::fusion_baseline::host_ids.count(item.first) == 1, "Unexpected deployed Host");
                need(deployed_host.insert(item.first).second, "Duplicate Host binding");
                continue;
            }
            need(item.second.same_as(zg_backend), "Unknown deployed backend");
            const auto found = info->hardop_map.find(item.first);
            need(found != info->hardop_map.end() && found->second.defined(), "Missing fused HardOp metadata");
            const auto entry = found->second;
            need(entry->net_hardop.defined() && entry->net_hardop->op_id == item.first, "Fused identity mismatch");
            need(groups.insert(item.first).second, "Duplicate ZG group");
            const auto sync = info->idx_map.find(item.first);
            need(sync != info->idx_map.end() && sync->second == entry->sync_idx, "Fused sync mismatch");
            need(sync->second.first >= 0 && sync->second.second > 0, "Invalid fused sync interval");
            need(ordered.emplace(sync->second.first,item.first).second, "Duplicate sync start");
            std::vector<int64_t> source(entry->merge_from.begin(), entry->merge_from.end());
            if (source.empty()) {
                need(hard.count(item.first) == 1, "Unmerged bound node is not an original HardOp");
                source.push_back(item.first);
            }
            need(std::set<int64_t>(source.begin(),source.end()).size() == source.size(), "Repeated merge member");
            for (auto id : source) need(hard.count(id) == 1 && effective.emplace(id,item.first).second,
                                       "Unknown or multiply covered original HardOp");
            pose_v1::fusion_baseline::members.emplace(item.first,source);
            pose_v1::fusion_baseline::sync.emplace(item.first,sync->second);
        }
        need(deployed_host == pose_v1::fusion_baseline::host_ids, "Incomplete direct Host coverage");
        need(!groups.empty() && effective.size() == 1158 && bindings.size() == groups.size()+6,
             "Incomplete fused coverage");
        expected_keys = hard;
        expected_keys.insert(groups.begin(),groups.end());
        for (const auto& item : info->hardop_map) map_keys.insert(item.first);
        for (const auto& item : info->idx_map) sync_keys.insert(item.first);
        need(map_keys == expected_keys && sync_keys == expected_keys, "Unexpected metadata coverage");
        for (const auto& item : info->hardop_map) {
            need(item.second.defined() && item.second->net_hardop.defined() &&
                 item.second->net_hardop->op_id == item.first, "Metadata identity changed");
            need(info->idx_map.at(item.first) == item.second->sync_idx, "Metadata sync changed");
            if (hard.count(item.first)) need(item.second->merge_from.empty(), "Original metadata unexpectedly merged");
        }
        uint32_t next = 0;
        for (const auto& item : ordered) {
            const auto span = pose_v1::fusion_baseline::sync.at(item.second);
            need(uint32_t(span.first) == next, "Gap or overlap in fused completion intervals");
            next += uint32_t(span.second);
            need(next <= 100000, "Unbounded runtime completion count");
        }
        pose_v1::fusion_baseline::final_count = next;
        auto bind = file(output / "bindings.jsonl");
        for (const auto& op : graph->ops) {
            const bool is_hard = op.is<xir::HardOp>();
            const auto target = is_hard ? effective.at(op->op_id) : op->op_id;
            bind << "{\"op_id\":" << op->op_id << ",\"operator\":" << quote(std::string(op->typeKey()))
                 << ",\"is_hardop\":" << (is_hard ? "true" : "false")
                 << ",\"effective_op_id\":" << target
                 << ",\"backend\":" << quote(std::string(bindings.at(target)->typeKey())) << "}\n";
        }
        auto summary = file(output / "binding-summary.json");
        summary << "{\"original_ops\":1164,\"original_hardops\":1158,\"direct_host_ops\":6,"
                << "\"effective_zg_groups\":" << groups.size() << ",\"coverage_complete\":true,"
                << "\"validated_runtime_final_count\":" << next << ",\"static_count_used_as_gate\":false}\n";
    }

