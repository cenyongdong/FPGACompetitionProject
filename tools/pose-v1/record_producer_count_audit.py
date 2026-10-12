"""Pin existing matched SDK ranges and current192 static producer identities."""
import json
import mixed_validation_gate as g
root=g.ROOT;old=root/'tools/pose-v1/evidence/startup-guard-20261009-r1';e=root/'tools/pose-v1/evidence/producer-count-20261009-r2'
audit=g.load(old/'SDK-mapping-review.json')
for name,digest in audit['artifact_sha256'].items():assert g.sha(old/name)==digest
udma=(old/'UDMA-read-audit.txt').read_text();dma=(old/'PLDDR-DMA-read-audit.txt').read_text()
assert '2c548:' in udma and 'pthread_mutex_lock@plt' in udma and '2c618:' in udma and 'memcpy@plt' in udma and '2c628:' in udma
assert '2c5a0:' in udma and '2c5e0:' in udma and '2c600:' in udma and 'write@plt' in udma
assert '2c5a4:' in udma and 'cmn\tx0, #0x1' in udma and '2c604:' in udma
assert '538e0:' in dma and 'pthread_mutex_lock@plt' in dma and '53b88:' in dma and 'MemChunk4read' in dma and '53b9c:' in dma
report=dict(status='matched_SDK_binary_paths_and192_static_mapping_audited_read_only',XRT_sha256=audit['XRT_sha256'],AXI_sha256=audit['AXI_sha256'],old_audit_sha256=g.sha(old/'SDK-mapping-review.json'),range_sha256={name:g.sha(old/name) for name in ('UDMA-read-audit.txt','PLDDR-DMA-read-audit.txt','UDMA-open-map-audit.txt')},UDMA_read_lock_object_offset='0x28',PLDDR_dmaRead_lock_object_offset='0x60',UDMA_source_CPTR_relative_offset=True,UDMA_read_length_argument=True,sync_offset_size_then_sync_for_cpu_before_memcpy=True,observed_write_error_check='return == -1; no full-written-length comparison identified in audited body',UDMA_memcpy_inside_read_lock=True,PLDDR_dmaRead_calls_MemChunk_read_before_unlock=True,application_private_offsets_or_pointers_used=False,matching_driver_source_verified=False,driver_sync_semantics_proven=False,root_cause_proven=False,application_zero_copy_mapping_verified=False,producer_values=[4386,4390],producer_ops=[8629,8631],group=9186,end_layer_count=234,diagnostic_queries_only=True,no_wait_change=True)
p=e/'SDK-path-audit.json';assert not p.exists();p.write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
