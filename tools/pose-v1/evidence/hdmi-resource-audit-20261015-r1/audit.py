"""Offline HDMI resource identity audit. No board, SDK, build or register access."""
from pathlib import Path
import hashlib
import json
import struct
from datetime import datetime, timezone, timedelta

ROOT = Path(r'D:\FPGACompetitionProject')
OUT = Path(__file__).resolve().parent
EXTERNAL = Path(r'D:\Dowload from Chrome\嵌赛资料\Icraft\参考实现')
REF = EXTERNAL / '单路PLIN+pHDMI/fpai_demo_package_26040701/fpai_demo_package_26040701'
BOOT = EXTERNAL / '位流/悟净LITE版_BOOT_25122301_单路PLIN+pHDMI(外置detpost)/悟净LITE版_BOOT_25122301_单路PLIN+pHDMI(外置detpost)'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def bit_payload(data):
    offset = 2 + struct.unpack_from('>H', data, 0)[0]
    if struct.unpack_from('>H', data, offset)[0] != 1:
        raise ValueError('Unexpected bit header')
    offset += 2
    fields = {}
    for tag in 'abcde':
        if data[offset:offset + 1] != tag.encode():
            raise ValueError('Unexpected bit field')
        offset += 1
        width = 4 if tag == 'e' else 2
        length = int.from_bytes(data[offset:offset + width], 'big')
        offset += width
        value = data[offset:offset + length]
        if len(value) != length:
            raise ValueError('Truncated bit field')
        if tag == 'e':
            if offset + length != len(data):
                raise ValueError('Trailing bit bytes')
            return value, fields
        fields[tag] = value.rstrip(b'\0').decode('ascii')
        offset += length
    raise ValueError('Missing bit payload')


def main():
    if (OUT / 'analysis.json').exists():
        raise RuntimeError('Preserve previous evidence; do not rerun in this directory')
    old = json.loads((ROOT / 'tools/pose-v1/evidence/boot-25122301-comparison-resolved.json').read_text(encoding='utf-8-sig'))
    boot_data = (BOOT / 'BOOT.bin').read_bytes()
    if digest(boot_data) != old['source_boot_sha256']:
        raise RuntimeError('BOOT identity differs; stop analysis')
    payload, header = bit_payload((BOOT / 'ai7030_top_disable_icap.bit').read_bytes())
    prior = old['pl_partition_from_supplied_log']
    offset, length = prior['byte_offset'], prior['bytes']
    partition = boot_data[offset:offset + length]
    if len(partition) != length or len(partition) % 4:
        raise RuntimeError('Invalid PL partition bounds')
    swapped = b''.join(partition[i:i + 4][::-1] for i in range(0, length, 4))
    if swapped[:len(payload)] != payload or swapped[len(payload):].hex() != '20000000':
        raise RuntimeError('BOOT/bit payload identity differs')
    source_paths = list(sorted(p for p in BOOT.iterdir() if p.is_file()))
    for rel in [
        'README.md', 'docs/API_REFERENCE.md', 'docs/BUILD_GUIDE.md',
        'examples/0_datapath/PLin+HDMI/README.md',
        'examples/0_datapath/PLin+HDMI/src/sdicamera+hdmi.cpp',
        'examples/0_datapath/PLin+HDMI/configs/ZG/sdicamera+hdmi.yaml',
        'deps/modelzoo_utils/include/et_device.hpp',
        'deps/modelzoo_utils/include/pipeline/io/input/sdicamera.hpp',
        'deps/modelzoo_utils/include/pipeline/io/output/hdmi_display.hpp',
        'deps/modelzoo_utils/include/pipeline/actor/hdmi_display_actor.hpp',
    ]:
        source_paths.append(REF / rel)
    for rel in [
        'Docs/26嵌赛开发/fpai_demo_fpga/rtl/ai7030_edif_top.v',
        'Docs/26嵌赛开发/fpai_demo_fpga/rtl/ps_ai_peripheral.sv',
        'Docs/26嵌赛开发/fpai_demo_fpga/rtl/sdi/rx_sdi.v',
        'Docs/26嵌赛开发/fpai_demo_fpga/rtl/utils/demo_clkrst_wrapper.v',
        'Docs/26嵌赛开发/fpai_demo_fpga/rtl/display/frame_to_ps_largebuf.v',
        'Docs/26嵌赛开发/fpai_demo_fpga/rtl/display/frame_trans.sv',
        'Docs/26嵌赛开发/fpai_demo_fpga/rtl/display/frame_ctrl.v',
        'Docs/26嵌赛开发/fpai_demo_fpga/rtl/display/frame_fifo_read.v',
        'Docs/26嵌赛开发/fpai_demo_fpga/rtl/display/color_bar.v',
        'Docs/26嵌赛开发/fpai_demo_fpga/rtl/display/video_define.v',
        'Docs/26嵌赛开发/fpai_demo_fpga/rtl/ip/cmos_clkgen_742_5/cmos_clkgen_742_5.xci',
        'software/core/display/display_worker.cpp', 'software/demo/board/main.cpp',
        'tools/pose-v1/evidence/boot-25122301-comparison-resolved.json',
        'tools/pose-v1/evidence/video-sequence-20261007-r1/hdmi-audit/inventory.json',
        'tools/pose-v1/evidence/video-sequence-20261007-r1/hdmi-audit/preflight.json',
        'tools/pose-v1/evidence/shared-stability-20261015-r2/final-cleanup-review.json',
    ]:
        source_paths.append(ROOT / rel)
    identical = []
    for rel in [
        'deps/modelzoo_utils/include/et_device.hpp',
        'deps/modelzoo_utils/include/pipeline/io/input/sdicamera.hpp',
        'deps/modelzoo_utils/include/pipeline/io/output/hdmi_display.hpp',
    ]:
        other = ROOT / 'Docs/26嵌赛开发/fpai_demo_app' / rel
        source_paths.append(other)
        equal = digest((REF / rel).read_bytes()) == digest(other.read_bytes())
        if not equal:
            raise RuntimeError('Reference copy differs: ' + rel)
        identical.append({'relative_path': rel, 'byte_identical': equal})
    sources = [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': digest(p.read_bytes())} for p in source_paths]
    (OUT / 'sources.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    result = {
        'date': datetime.now(timezone(timedelta(hours=8))).isoformat(),
        'execution': {'platform': 'Windows; Python standard library', 'cwd': str(ROOT), 'scope': 'offline static analysis and file identity checks'},
        'source_boot': {'path': str(BOOT / 'BOOT.bin'), 'bytes': len(boot_data), 'sha256': digest(boot_data)},
        'matches_historical_board_boot': digest(boot_data) == old['board_boot_sha256'],
        'historical_board_record_is_not_new_live_read': True,
        'paired_bit': {'header': header, 'payload_bytes': len(payload), 'payload_sha256': digest(payload), 'word_swapped_BOOT_prefix_equal': True, 'partition_offset_from_existing_log': offset, 'partition_bytes': length, 'padding_hex': swapped[len(payload):].hex()},
        'reference_software': {'package': '26040701', 'declared_target': 'ZG / AI Mate 25122301 / single PLIN+pHDMI', 'icraft': '3.36.0', 'current_project_sdk': '3.39.0', 'duplicated_headers': identical},
        'static_findings': [
            'Example constructs SDICamera before HDMI display; camera config initializes resize/capture settings and input VTC selection.',
            'Display fps YAML is not parsed by the no-AI example; display width/height do not program PLL or HDMI timing.',
            'In reference RTL, programmable H/V registers feed input VTC; HDMI HS/VS/DE originate from color_bar, with VIDEO_1920_1080 selected.',
            'Reference HDMI reader has fixed width 1920, height 1080 and read_len=518400 64-bit words, or 4147200 bytes.',
            'Reference rx_sdi selects cam_clk=rx0_locked ? rx_usrclk : sys_clk_200m; top connects fallback input to hp_clk. Actual current bitstream clock topology/frequency is unverified.',
            'Reference serializer PCLKX1 uses cam_clk directly; PLL clk_out1 is not its selected pixel clock. Input VTC enable cannot by itself establish correct HDMI clock.',
            'Reference camera_rd_addr+0x54 matches software address/8 convention; reader latches address on request, but software-visible flip completion/stop-drain contract is not established.',
            'Reference read_finish is unconnected at frame_to_ps instantiation; disable_hdmi gates timing but is not proven outstanding-DDR-read completion.',
        ],
        'unproven': ['Exact editable RTL/build correspondence to selected BOOT', 'Current board actual HDMI pixel/serial clock and monitor mode', 'No-SDI clock hypothesis as physical root cause', 'Safe register applicability and read-only register whitelist for current hardware', 'Safe scanout start, flip, stop and buffer-release protocol'],
        'no_board_connection_or_MMIO': True, 'no_build_or_bitstream_download': True, 'no_BOOT_SDK_model_changes': True,
        'current_hdmi_acceptance': 'not verified', 'old_DATA_investigation': 'remains paused',
    }
    (OUT / 'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'offline_identity_checks_passed', 'boot_matches_historical_board': result['matches_historical_board_boot'], 'paired_bit_payload_matches': True, 'reference_sources': len(sources), 'HDMI_hardware_verified': False}))


if __name__ == '__main__':
    main()
