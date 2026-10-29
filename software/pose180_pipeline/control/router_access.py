"""Task-local owned-router access; credentials/cookies stay only in memory."""
import argparse
import base64
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
import time
import requests

ROOT=Path(__file__).resolve().parents[3]
HOSTS={'rx1':'192.168.50.1','tx':'192.168.50.2','rx2':'192.168.50.3','rx3':'192.168.50.4'}
OUT=ROOT/'.local/pose180-resident-20261025/routers'

def credentials(host):
    for line in (ROOT/'Agents.md').read_text(encoding='utf-8-sig').splitlines():
        columns=[x.strip() for x in line.split('|')]
        if len(columns)>6 and columns[3]==host:return columns[4],columns[5].encode()
    raise ValueError('Authorized router credential missing')

def main():
    p=argparse.ArgumentParser();p.add_argument('kind',choices=HOSTS);p.add_argument('label');p.add_argument('mode',choices=('http-read','http-enable','http-restore','exec','put','get'));p.add_argument('source',nargs='?');p.add_argument('destination',nargs='?');p.add_argument('--timeout',type=int,default=30);a=p.parse_args()
    if not re.fullmatch('[a-zA-Z0-9_-]+',a.label):raise ValueError('Invalid label')
    directory=OUT/a.kind;directory.mkdir(parents=True,exist_ok=True)
    receipt=directory/(a.label+'.json')
    if receipt.exists():raise ValueError('Preserve prior receipt')
    host=HOSTS[a.kind];user,password=credentials(host)
    if a.mode.startswith('http-'):
        base='http://'+host
        with requests.Session() as session:
            session.headers.update({'Referer':base+'/Main_Login.asp','Origin':base,'User-Agent':'Mozilla/5.0'})
            login=session.post(base+'/login.cgi',data={'login_authorization':base64.b64encode(user.encode()+b':'+password).decode(),'next_page':'Advanced_System_Content.asp'},timeout=8)
            login.raise_for_status()
            page=session.get(base+'/Advanced_System_Content.asp',timeout=8);page.raise_for_status()
            if 'name="sshd_enable"' not in page.text:raise ValueError('Router login/system page unavailable; no retry')
            if a.mode!='http-read':
                # Same existing administrator, LAN-only access, no WAN, new key,
                # password change, radio change or router reboot.
                wanted='2' if a.mode=='http-enable' else '0'
                current=re.search(r'<option value="([012])" selected>',re.search(r'<select name="sshd_enable".*?</select>',page.text,re.S).group(0)).group(1)
                if a.mode=='http-enable' and current!='0':raise ValueError('SSH baseline changed; inspect before applying')
                applied=session.post(base+'/start_apply.htm',data={'action_mode':'apply','action_script':'restart_sshd',
                    'action_wait':'5','current_page':'Advanced_System_Content.asp','next_page':'Advanced_System_Content.asp',
                    'sshd_enable':wanted,'sshd_port':'22' if wanted=='2' else '', 'sshd_pass':'1'},timeout=10)
                applied.raise_for_status();time.sleep(2)
                page=session.get(base+'/Advanced_System_Content.asp',timeout=8)
                selector=re.search(r'<select name="sshd_enable".*?</select>',page.text,re.S)
                if not selector or not re.search(r'<option value="'+wanted+'" selected>',selector.group(0)):raise ValueError('SSH setting not confirmed; no apply retry')
                result={'host':host,'mode':a.mode,'sshd_enable':wanted,'LAN_only':wanted=='2','prior':current,'HTTP_status':applied.status_code}
                session.get(base+'/Logout.asp',timeout=8)
                receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return 0
            lines=[line.strip() for line in page.text.splitlines() if any(x in line for x in ('sshd_enable','sshd_port','sshd_pass','sshd_wan','sshd_authkeys','action_script','action_mode','<form'))]
            # Never serialize credentials, session cookies or authentication keys.
            lines=[line for line in lines if 'authkeys' not in line]
            selector=re.search(r'<select name="sshd_enable".*?</select>',page.text,re.S)
            api=session.get(base+'/js/httpApi.js',timeout=8)
            method=re.search(r'nvramSet\s*:\s*function.*?\n\s*},',api.text,re.S)
            result={'host':host,'mode':a.mode,'fields':lines,'ssh_choices':selector.group(0) if selector else None,
                    'apply_api':method.group(0)[:2500] if method else None}
            session.get(base+'/Logout.asp',timeout=8)
    else:
        source=ROOT/'tools/nexmon/host/router_transport.py'
        spec=importlib.util.spec_from_file_location('resident_router_transport',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        known=directory/'known_hosts'
        if not known.exists():shutil.copyfile(ROOT/'tools/nexmon/evidence/multirx-20261025-r1'/a.kind/'auth-live/known_hosts',known)
        (directory/'askpass.sh').write_text('#!/bin/sh\nexec "'+Path(sys.executable).as_posix()+'" "'+source.as_posix()+'" askpass "$@"\n',newline='\n')
        data=None
        if a.mode=='exec':script=Path(a.source).read_text(encoding='utf-8-sig')
        elif a.mode=='put':
            target=module.remote_path(a.destination);script='umask 077; test ! -e '+target+' && cat > '+target;data=Path(a.source).read_bytes()
        else:script='cat '+module.remote_path(a.source)
        code,stdout,stderr=module.ssh_run(directory,user,password,script,data,a.timeout,host)
        if a.mode=='get':
            with Path(a.destination).open('xb') as file:file.write(stdout)
            result={'host':host,'exit_code':code,'bytes':len(stdout),'stderr':stderr.decode(errors='replace')}
        else:result={'host':host,'exit_code':code,'stdout':stdout.decode(errors='replace'),'stderr':stderr.decode(errors='replace')}
    password=b''
    receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
    return result.get('exit_code',0)

if __name__=='__main__':raise SystemExit(main())
