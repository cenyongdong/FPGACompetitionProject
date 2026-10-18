"""Reproduce offline qualification against its real recorded execution context.

No state file is changed or fabricated. Only the two historical build guards
read their preserved context. Real stage/UART/BOOT permissions read live STATE.
"""
from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parents[3]
STATE=ROOT/'tools/pose-v1/evidence/hdmi-live-20261017-r3/continuation-state.json'
SNAPSHOT=ROOT/'tools/pose-v1/evidence/hdmi-live-20261018-r9/state-read-v3r9-native-bit-r3-start/after.json'
SNAPSHOT_SHA='70356375b938bee4103cc94511d76bc99c9243454ef0b60f693ac6a7c00958c4'
FINAL='16adc4a988f59d7064d1fa19b26f9bd8765217341921ca84f103f0465bcdfc3b'
REPORTS='528fa208e01a3de18f3f312ce929458ea5c94dc59845dae2e4f036bf79f00967'
DRIVER='3e65b5154282f5c714576bde337f01cb34cdf1a4197a7e0a4f072557d86991c5'
BIT='c42c3340b024e0cfe1f8cb7f2c63ba614c5f5ede9b9a74f0b4e327f6eac98189'


def qualification_state():
    raw=SNAPSHOT.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SNAPSHOT_SHA:raise ValueError('Actual qualification context changed')
    value=json.loads(raw)
    if (value['whole_task_pause']['paused'] or not value['offline_work_continues']
            or not value['onsite_observation_work']['paused'] or value['BOOT_writes_authorized']
            or value['old_DATA']!='paused' or value['remaining_previous_package_reboots']!=0):
        raise ValueError('Preserved qualification boundaries differ')
    return value


def build_guard_load(original):
    def load(path):
        if Path(path).resolve()==STATE.resolve():return qualification_state()
        return original(path)
    return load


def bind(backend):
    """Instance-local loader adapters; original source and decision code retained."""
    qualification_state()
    if getattr(backend,'qualification_context_bound',False):return backend
    original_module=backend.module

    def module(path,expected=None,name='r9_release_input'):
        result=original_module(path,expected,name)
        basename=Path(path).name
        if basename=='review_hdmi_reader_boundary_factory_route.py':
            if expected!=FINAL:raise ValueError('Unexpected final qualifier source')
            original_final_loader=result.module

            def final_loader(filename,digest):
                reports=original_final_loader(filename,digest)
                if filename=='continue_hdmi_reader_boundary_reports.py':
                    if digest!=REPORTS:raise ValueError('Unexpected historical reports source')
                    reports.load=build_guard_load(reports.load)
                    original_frozen=reports.frozen

                    def frozen(filename):
                        loaded=original_frozen(filename)
                        if filename=='continue_hdmi_reader_boundary_candidate.py':
                            if reports.PINS[filename]!=DRIVER:raise ValueError('Unexpected build source')
                            loaded.load=build_guard_load(loaded.load)
                        return loaded
                    reports.frozen=frozen
                return reports
            result.module=final_loader
        elif basename=='continue_hdmi_reader_boundary_bit_r3.py':
            if expected!=BIT:raise ValueError('Unexpected actual executed bit source')
            original_release=result.release
            result.release=lambda:bind(original_release())
        return result

    backend.module=module
    backend.qualification_context_bound=True
    return backend


def proof():
    qualification_state()
    return dict(recorded_qualification_state=str(SNAPSHOT),SHA256=SNAPSHOT_SHA,
                exact_source_and_all_report_decisions_retained=True,
                live_state_file_changed=False,execution_permission_created=False,
                current_execution_pause_and_approval_checked_separately=True)
