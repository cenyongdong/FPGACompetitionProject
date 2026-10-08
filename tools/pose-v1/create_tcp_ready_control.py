"""Correct only the external not-yet-listening startup rendezvous; freeze r1."""
from pathlib import Path
root=Path(__file__).resolve().parent
sender=(root/'send_live_windows.py').read_text(encoding='utf-8')
sender=sender.replace("report=dict(status='not_completed',fps=2,sent=[],startup_wait_only=True)","report=dict(status='not_completed',fps=2,sent=[],startup_wait_only=True,startup_attempts=[])")
sender=sender.replace('            except ConnectionRefusedError:', '            except (ConnectionRefusedError, TimeoutError) as error:\n                report[\'startup_attempts\'].append(dict(kind=type(error).__name__,remaining_s=max(0,deadline-time.monotonic())))')
path=root/'send_live_windows_ready.py';assert not path.exists();path.write_bytes(sender.encode())
peer=(root/'tcp_live_peer.py').read_text(encoding='utf-8')
peer=peer.replace('import argparse,json,subprocess,sys','import argparse,hashlib,json,subprocess,sys')
peer=peer.replace('send_live_windows.py','send_live_windows_ready.py')
peer=peer.replace("    sender=subprocess.Popen", "    provenance={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in (Path(__file__).name,'send_live_windows_ready.py')}\n    (a.output/'controller-sources.json').write_bytes((json.dumps(provenance,indent=2)+'\\n').encode())\n    sender=subprocess.Popen")
path=root/'tcp_live_peer_ready.py';assert not path.exists();path.write_bytes(peer.encode())
