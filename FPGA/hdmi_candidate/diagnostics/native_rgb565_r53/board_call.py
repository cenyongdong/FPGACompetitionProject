from pathlib import Path
import argparse,importlib.util,sys,json,contextlib,os
R=Path('D:\\FPGACompetitionProject');E=Path('D:\\FPGACompetitionProject\\tools\\pose-v1\\evidence\\hdmi-pipeline-20261024-r53')
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('mode',choices=['ssh','put','get']);p.add_argument('source');p.add_argument('destination',nargs='?');p.add_argument('--timeout',type=int,default=120);a=p.parse_args()
spec=importlib.util.spec_from_file_location('pinned_transport',Path(__file__).with_name('native_transport.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.REMOTE='/root/hdmi-pipeline-20261024-r53/'
log=E/(a.name+'.log');sys.argv=[str(m.__file__),a.mode,a.source]
if a.destination:sys.argv.append(a.destination)
sys.argv+=['--timeout',str(a.timeout),'--log',str(log)]
with open(os.devnull,'w') as null,contextlib.redirect_stdout(null):code=m.main()
print(json.dumps(dict(operation=a.name,exit_code=code,raw_log=str(log))))
if a.mode=='ssh' and log.exists():print(log.read_text(errors='replace')[-1800:])
raise SystemExit(code)
