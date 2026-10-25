"""Summarize actual zero-frame failure and verified original-runtime recovery."""
from pathlib import Path
import json, tarfile

root = Path('D:/FPGACompetitionProject')
e = root / 'tools/pose-v1/evidence/hdmi-long-native-20261024-r48'
with tarfile.open(e / 'candidate-evidence.tar.gz') as tar:
    def record(name):
        return json.load(tar.extractfile(name))
    admission = record('startup-admission.json')
    seed = record('startup/before-seed.json')
    native = record('metadata/long-test.json')
    hdmi = [json.loads(x) for x in tar.extractfile('software/run-long-native/results/hdmi.jsonl').read().decode().splitlines()]
host = json.loads((e / 'host/summary.json').read_text())
closed = json.loads((e / 'closed.json').read_text())
audit = json.loads((e / 'final-audit.json').read_text())
recovered = (closed['closed'] and closed['boot_id'] == audit['boot_id'] and
             len(audit['startup_files']) == 9 and len(audit['SDK']) == 6 and
             audit['fpga_state'] == 'operating')
summary = dict(passed=False, completed_frames=host['received'], host_sent=host['sent'],
               host_errors=host['errors'], startup=admission['startup_classification'],
               startup_mode=admission['mode'], startup_PS_AR=seed['PS_AR'], startup_PS_R=seed['PS_R'],
               native_exit=native['native_exit'], native_seconds=native['seconds'],
               HDMI_adopted=native['HDMI_adopted'],
               HDMI_START_commands=sum(x.get('event') == 'command' and x.get('op') == 1 for x in hdmi),
               STOP_proved=any(x.get('event') == 'stop_proved' for x in hdmi),
               frames_released=any(x.get('event') == 'frames_released_after_stop' for x in hdmi),
               protocol_snapshots=native['protocol_snapshots'],
               fresh_native_protocol_clean=native['all_fresh_native_protocol_checks_passed'],
               original_runtime_restored=recovered, original_runtime_boot_id=audit['boot_id'],
               original_BOOT_sha256=audit['startup_files']['BOOT.BIN']['sha256'],
               original_files_verified=len(audit['startup_files']), SDK_files_verified=len(audit['SDK']),
               actual=dict(candidate_starts=1, original_fallbacks=1, SDK_Open=1),
               remaining=dict(candidate_starts=0, original_fallbacks=0, SDK_Open=0),
               hardware_rebuilt=False, AI_four_HC_unchanged=True,
               physical_screen_verified=False, long_stability_proved=False,
               failed_r46_not_reclassified=True, automatic_retry=False)
(e / 'result-summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
state = json.loads((e / 'state.json').read_text())
state.update(status='closed_zero_frame_host_spawn_failure_original_restored', active=False,
             actual=summary['actual'], remaining=summary['remaining'],
             original_runtime_boot_id=audit['boot_id'],
             original_BOOT_file_restored=True, original_runtime_restored=recovered,
             completed_frames=host['received'], long_stability_proved=False,
             result='result-summary.json', BOOT_current_sha256=summary['original_BOOT_sha256'])
(e / 'state.json').write_text(json.dumps(state, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False))
