"""Read Vivado 2019.1's actual PS7 library contract, without loading failed PS RTL.

This metadata probe never replaces databases or constructs an artificial PS model.
The small anchor design only opens the standard device library for read-only queries.
"""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, time

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-vivado2019-library-20261015-r1'
W = R / '.local/hdmi-vivado2019-library-20261015-r1'
E.mkdir(exist_ok=False)
W.mkdir(exist_ok=False)
(W / 'anchor.v').write_text('module metadata_anchor(input a, output y); assign y=a; endmodule\n', encoding='ascii')
script = '''
if {[catch {
 create_project -in_memory -part xc7z030ffg676-2
 read_verilog anchor.v
 synth_design -rtl -top metadata_anchor -part xc7z030ffg676-2
 set cells [get_lib_cells -quiet *PS7*]
 puts "METADATA_PS7_LIBRARY_CELLS $cells"
 set f [open {PINFILE} w]
 foreach cell $cells {
  puts $f "CELL|$cell"
  report_property $cell
  foreach pin [get_lib_pins -of_objects $cell] {
   puts $f "$pin|[get_property DIRECTION $pin]"
  }
 }
 close $f
 close_design
 close_project
 puts "METADATA_QUERY_FINISHED"
} result]} {puts "METADATA_QUERY_FAILED $result";exit 1}
exit
'''.replace('PINFILE', (E / 'builtin-PS7-pins.txt').as_posix())
(W / 'query.tcl').write_text(script, encoding='ascii')
for n in ('query.tcl', 'anchor.v'):
 shutil.copyfile(W / n, E / n)
env = os.environ.copy()
env['PROCESSOR_ARCHITECTURE'] = 'AMD64'
args = ['D:/Xilinx/Vivado/2019.1/bin/vivado.bat', '-mode', 'batch', '-nojournal',
        '-log', str(E / 'vivado.log'), '-source', str(W / 'query.tcl')]
start = time.monotonic()
timeout = False
with (E / 'stdout.txt').open('wb') as out, (E / 'stderr.txt').open('wb') as err:
 p = subprocess.Popen(args, cwd=W, env=env, stdout=out, stderr=err,
                      creationflags=subprocess.CREATE_NO_WINDOW)
 try:
  code = p.wait(timeout=60)
 except subprocess.TimeoutExpired:
  timeout = True
  clean = subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'], capture_output=True, timeout=15)
  (E / 'cleanup.txt').write_bytes(clean.stdout + clean.stderr)
  code = p.wait(timeout=15)
result = {'exit': code, 'seconds': time.monotonic() - start, 'budget_seconds': 60,
          'timeout': timeout, 'actual_PS_RTL_retried': False,
          'project_local_metadata_query_only': True, 'global_database_write': False,
          'hardware_gate_or_migration_pass': False}
(E / 'execution.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result), flush=True)
print((E / 'stdout.txt').read_text(errors='replace')[-2000:], flush=True)
if code or timeout:
 raise SystemExit('Metadata query failed; preserve and stop')
