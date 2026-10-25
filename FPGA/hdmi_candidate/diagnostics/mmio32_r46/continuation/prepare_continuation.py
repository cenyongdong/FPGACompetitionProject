"""Prepare the expressly approved same-boot diagnostic continuation. No board IO."""
from pathlib import Path
import json, shutil, hashlib
W=Path(__file__).resolve().parent
E=Path('D:/FPGACompetitionProject/tools/pose-v1/evidence/hp2-mmio32-20261024-r46')
D=W/'continuation'; P=D/'package'; P.mkdir(parents=True,exist_ok=True)
for name in ('capture_deferred.py','consume_gate.py','r45_diagnostic_stages.py'):
    shutil.copyfile(E/'deploy/package'/name,P/name)
text=(P/'capture_deferred.py').read_text().replace('release[7] == 1,','release[7] == h[\'request\']//2,')
(P/'capture_deferred.py').write_text(text)

text=(P/'consume_gate.py').read_text()
text=text.replace('def _native(protocol):','def _native(protocol, consumption_underflow=False):')
text=text.replace('    if "live_status" in protocol:\n        values.append(protocol["live_status"])\n','')
old='    _need(bool(bits & KNOWN) and bits <= ALLOWED, "Missing known rule or unexpected native checks: " + str(sorted(bits)))\n    return bits'
new='''    # Frozen startup history is never granted the consumption-only exception.
    _need(bool(bits & KNOWN) and bits <= ALLOWED,
          "Missing known rule or unexpected historical checks: " + str(sorted(bits)))
    if "live_status" in protocol:
        live = _uint(protocol["live_status"], "live native status", 160)
        bits.update(i for i in range(160) if live >> i & 1)
    allowed = ALLOWED | ({79} if consumption_underflow else set())
    _need(bits <= allowed, "Unexpected live native checks: " + str(sorted(bits)))
    return bits'''
assert old in text;text=text.replace(old,new)
text=text.replace('before_bits, after_bits = _native(protocol_before), _native(protocol_after)',
    'before_bits, after_bits = _native(protocol_before), _native(protocol_after, consumption_underflow=True)')
text=text.replace('protocol_history_preserved=True, native_check_bits=sorted(after_bits))',
    'protocol_history_preserved=True, native_check_bits=sorted(after_bits),\n                   consumption_CAM_underflow_retained=79 in after_bits,\n                   checker_only_rearm_required=True, fresh_functional_160_bit_gate_unchanged=True)')
(P/'consume_gate.py').write_text(text)

text=(P/'r45_diagnostic_stages.py').read_text()
text=text.replace("'consume', 'cycletrace-after'","'consume', 'revalidate-consume', 'cycletrace-after'")
text=text.replace('def _capture(run, stage):\n    value = _read(run/stage/\'capture/result.json\')',
'''def _consume_result_path(run):
    return run/'revalidate-consume/capture/result.json'


def _capture(run, stage):
    path = _consume_result_path(run) if stage == 'consume' else run/stage/'capture/result.json'
    value = _read(path)''')
text=text.replace("    value = _read(run/'metadata'/(stage+'.json'))", "    source = 'revalidate-consume' if stage == 'consume' else stage\n    value = _read(run/'metadata'/(source+'.json'))")
text=text.replace("str(run/'consume/capture/result.json')","str(_consume_result_path(run))")
text=text.replace("        if stage in ('observe-before','consume','checker-rearm'):",
'''        if stage == 'revalidate-consume':
            import revalidate_consume
            out = run/stage/'capture'
            out.mkdir(parents=True, mode=0o700)
            value = revalidate_consume.revalidate(run,boot_id)
            c.fresh_json(out/'result.json',value)
            result.update(valid=True,passed=True,original_failure_preserved=True,
                          original_raw_sha256=value['original_raw_sha256'],
                          observer_generation=value['normalized']['observer_generation'],
                          MMIO_commands=0,SDK=0,DMA=0,HDMI_START=0)
        elif stage in ('observe-before','consume','checker-rearm'):''')
(P/'r45_diagnostic_stages.py').write_text(text)

text=(E/'deploy/ps_release_board.py').read_text()
text=text.replace("'cycletrace-after','protocol-after','consumed-gate'","'revalidate-consume','cycletrace-after','protocol-after','consumed-gate'")
text=text.replace("CODE_FILES=('r45_diagnostic_stages.py',","CODE_FILES=('revalidate_consume.py','r45_diagnostic_stages.py',")
text=text.replace("def stopped():\n    return (ROOT_META/'stopped.json').exists()",'''def parser_resolution_valid():
    path=ROOT_META/'consume-parser-resolution.json'
    if not path.exists():return False
    receipt=read(path);stop=root('stopped')
    raw=BASE/'run-1/consume/capture/raw.jsonl'
    return (cfg.get('same_boot_continuation',{}).get('approved') is True and
            receipt.get('valid') is True and receipt.get('boot_id')==b.boot_id()==stop.get('boot_id') and
            stop.get('stage')=='consume' and stop.get('cycle')==1 and
            receipt.get('MMIO_commands')==0 and receipt.get('original_failure_preserved') is True and
            receipt.get('original_raw_sha256')==b.digest(raw))


def stopped():
    return ((ROOT_META/'diagnostic-continuation-stopped.json').exists() or
            ((ROOT_META/'stopped.json').exists() and not parser_resolution_valid()))''')
text=text.replace("    save(ROOT_META/'stopped.json',dict(stage=stage", "    target=ROOT_META/('diagnostic-continuation-stopped.json' if (ROOT_META/'stopped.json').exists() else 'stopped.json')\n    save(target,dict(stage=stage")
text=text.replace("after=read(run/'consume/capture/result.json')['normalized']", "after=read(run/'revalidate-consume/capture/result.json')['normalized']")
text=text.replace("    if stage=='audit':return b.audit(ORIGINAL)",'''    continuation=cfg.get('same_boot_continuation',{})
    b.need(continuation.get('approved') is True and
           continuation.get('boot_id')==b.boot_id() or stage in ('audit','close'),
           'Approved same-boot continuation identity differs')
    allowed={'audit','revalidate-consume','cycletrace-after','protocol-after','consumed-gate',
             'checker-rearm','frame-test','post-frame-protocol','joint-test','post-joint-protocol',
             'fallback-reboot','close'}
    b.need(stage in allowed,'No new consume, functional reset or candidate start in this continuation')
    if stage=='audit':return b.audit(ORIGINAL)''')
text=text.replace("b.need(not stopped() or recovery_evidence,'Unknown/failed action already stopped r45')",
    "b.need(not stopped() or recovery_evidence or (stage=='revalidate-consume' and not (ROOT_META/'diagnostic-continuation-stopped.json').exists()),'Unknown/failed action already stopped r45')")
text=text.replace("        if not result.get('valid',False):mark_stopped(stage,n,result)\n        return result",'''        if not result.get('valid',False):mark_stopped(stage,n,result)
        elif stage=='revalidate-consume':save(ROOT_META/'consume-parser-resolution.json',result)
        return result''')
(D/'ps_release_board.py').write_text(text)

def identity(p):return dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
cfg=json.loads((E/'deploy/config.json').read_text())
cfg['same_boot_continuation']=dict(approved=True,boot_id='ca5ae553-4b37-4daf-b30c-84746f081176',
    user_authorization='2026-10-24 明确同意保留失败及79历史，同次启动checker-only rearm，全160位新鲜门通过再两图案及90窗；不再消费/功能复位/新增候选，最多2SDK，异常停并原BOOT回退。',
    new_candidate_starts=0,new_consume_commands=0,functional_resets=0,mandatory_fresh_PC_mask_unchanged=True)
cfg['controller_files']['ps_release_board.py']=identity(D/'ps_release_board.py')
for p in P.glob('*.py'):cfg['files'][p.name]=identity(p)
(D/'config.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared same-boot continuation; no board access. Finalize after adding offline revalidator.')
