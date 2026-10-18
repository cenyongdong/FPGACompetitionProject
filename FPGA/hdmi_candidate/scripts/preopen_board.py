"""r13 proposal: observe the unchanged r9 CSR before any SDK Open, then gate all loads."""
import argparse,json,os,traceback
from pathlib import Path
import timing_board as t

b=t.b;cfg=t.cfg;common=t.common;ROOT=t.ROOT;PACKAGE=t.PACKAGE

def main(stage):
    if stage=='preopen':
        t.guard();exe=PACKAGE/'ai_preopen_monitor';b.verify_file(exe,cfg['files']['ai_preopen_monitor']);os.chmod(exe,0o700)
        output,process=t.execute('preopen',[str(exe),str(ROOT/'preopen/trace.jsonl')])
        result=dict(passed=False,process=process,SDK_opened=False)
        if process['exit_code']==0:
            x=json.loads((output/'trace.jsonl').read_text());w=x['words']
            b.need(len(w)==104 and w[0]==0x41495201 and x['request']==x['response']==2 and x['status']==0,'Pre-Open raw extent/generation invalid')
            result['snapshot']=x
            result['passed']=w[3]==0 and (w[2]&0x1f)==0x19 and all(w[8+16*c]==w[8+16*c+1]==0 for c in range(6)) and w[8+16*4+7]==0
            result['classification']='idle_before_SDK' if result['passed'] else 'abnormal_before_SDK_no_Device_Open'
        return common.save('preopen',result)
    if stage=='full-dma':
        t.guard();b.need(common.record('preopen')['passed'],'Pre-Open observation abnormal: no Device::Open')
        exe=PACKAGE/'ai_read_segmented_probe';b.verify_file(exe,cfg['files']['ai_read_segmented_probe']);os.chmod(exe,0o700)
        name='full-dma';out,process=t.execute(name,[str(exe),str(ROOT/name/'trace.jsonl'),'20','20','2','1048576'])
        result=t.compare_dma(out,process,2,[64,4096,65536,1048576]);return common.save(name,result)
    if stage=='shared':
        t.guard();gate=common.record('full-dma');b.need(gate['passed'] and gate['sequence_after']==12,'Complete four-size gate absent')
        t.verify_shared();target=PACKAGE/'shared-package'
        out,process=t.execute('shared',[str(target/'pose_hdmi_demo'),str(target),str(ROOT/'shared/inference'),'--allow-device-init'])
        return common.save('shared',dict(process,independent_numeric_and_HDMI_review_required=True,visual_confirmation_required=True))
    return t.main(stage)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','install','candidate-reboot','restore','preopen','full-dma','shared','fallback-reboot','audit','close']);args=parser.parse_args()
    try:print(json.dumps(main(args.stage),ensure_ascii=False,indent=2),flush=True)
    except BaseException:traceback.print_exc();raise SystemExit(1)
