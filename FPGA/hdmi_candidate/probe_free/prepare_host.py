"""Prepare pinned transports and receive-only UART; reuse router autostart."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / '.local/hdmi-probe-free-20261025-r1'
OLD = ROOT / '.local/pose180-resident-witness-20261025-r9'


def write(path, text):
    path.write_text(text, encoding='utf-8-sig' if path.suffix=='.ps1' else 'utf-8', newline='\n')


def main():
    for name in ('board_call.py','router_call.py',
                 'capture_hdmi_startup.ps1','capture_uart.py',
                 'add-management-ip.ps1','remove-management-ip.ps1'):
        text=(OLD/name).read_text(encoding='utf-8-sig')
        text=text.replace(OLD.name,WORK.name)
        if name=='capture_uart.py':
            text=text.replace("('candidate-1','fallback')", "('candidate-1','candidate-2','candidate-3','fallback')")
        write(WORK/name,text)
    for index in range(1,4):
        text=(OLD/'board_network.py').read_text().replace(OLD.name+'/network',WORK.name+'/round-'+str(index)+'/network')
        write(WORK/('round-'+str(index)+'-network.py'),text)
    print('Prepared three finite boot captures and pinned transports; reuse the separately verified router autostart services.')


if __name__=='__main__':main()
