"""Read original local documentation and MIG configuration; no board access."""
from pathlib import Path
import hashlib,json,shutil,zipfile,xml.etree.ElementTree as ET
from pypdf import PdfReader

R=Path(__file__).resolve().parents[4]
E=Path(__file__).resolve().parent
assert not (E/'analysis.json').exists()
names=('ARCHITECTURE-DISCUSSION-20261015.md','Done.md','DIFFICULTIES.md')
(E/'before').mkdir()
for n in names:shutil.copyfile(R/n,E/'before'/n)
fpga=R/'Docs/26嵌赛开发/fpai_demo_fpga'
paths=[R/'Docs/26嵌赛开发/30TAI使用教程.pdf',R/'Docs/26嵌赛开发/FPAI_DEMO说明.pdf',
 fpga/'rtl/ip/mig_7series_0/mig_7series_0.xci',fpga/'rtl/ip/mig_7series_0/mig_b.prj',
 fpga/'rtl/ps_ai_peripheral.sv',fpga/'rtl/utils/demo_clkrst_wrapper.v',fpga/'rtl/sdi/rx_sdi.v',
 fpga/'rtl/display/frame_to_ps_largebuf.v',fpga/'rtl/display/frame_fifo_read.v',fpga/'vivado.log']
identity=[{'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
pdf_pages={}
for p in paths[:2]:
    pdf_pages[p.name]=[{'page':n,'text':page.extract_text()} for n,page in enumerate(PdfReader(p).pages,1)]
(E/'original-pdf-text.json').write_text(json.dumps(pdf_pages,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ns={'s':'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009'}
xci=ET.parse(paths[2]).getroot()
params={x.attrib.get('{'+ns['s']+'}referenceId'):x.text for x in xci.findall('.//s:configurableElementValue',ns)}
assert params['PARAM_VALUE.XML_INPUT_FILE']=='mig_b.prj'
mig=ET.parse(paths[3]).getroot()
period=float(mig.findtext('.//TimePeriod'))
ratio=mig.findtext('.//PHYRatio')
assert period==1250 and ratio=='4:1'
ddr_mhz=1e6/period
ui_mhz=ddr_mhz/4
zips=[]
for p in Path('D:/Dowload from Chrome/嵌赛资料/Icraft/参考实现').rglob('*.zip'):
    with zipfile.ZipFile(p) as z:
        entries=z.namelist()
        zips.append({'path':str(p),'entries':len(entries),'hardware_or_report_entries':[n for n in entries if n.lower().endswith(('.v','.sv','.xpr','.rpt','.ltx','.sdc','.fdc','.xdc','.pdf','.docx'))]})
result={'scope':'local_only_no_board_or_build','sources':identity,'archives':zips,
 'MIG_selected_project':params['PARAM_VALUE.XML_INPUT_FILE'],'memory_period_ps':period,'PHYRatio':ratio,
 'reference_DDR_clock_MHz':ddr_mhz,'reference_UI_fallback_MHz':ui_mhz,
 'conditional_1080p_refresh_Hz':ui_mhz*1e6/(2200*1125),'conditional_serial_clock_MHz':ui_mhz*5,
 'interpretation':'Source configuration inference only. Neither current BOOT build identity nor live pixel/PLL measurement is established.',
 'documentation':'30TAI tutorial pages 10-11 explicitly describe no-SDI camera.vtc=true HDMI rolling grayscale; this is the complete camera-test pipeline, not proof of independent PS-only display or safe-stop API.'}
(E/'analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('sources','archives')},ensure_ascii=False))
