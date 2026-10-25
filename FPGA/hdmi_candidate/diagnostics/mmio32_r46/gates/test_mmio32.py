"""CPU ordinary-memory ctypes calls and instruction checks; no device mapping."""
import ctypes
import json
from pathlib import Path
import re
import struct
import sys
from types import SimpleNamespace

sys.dont_write_bytecode=True
import capture_deferred as c

ROOT=Path(__file__).resolve().parents[1]


class Evidence:
    def __init__(self):self.events=[]
    def save(self,event,**values):self.events.append(dict(event=event,**values))


def main():
    cases=[]
    def check(name,action):
        try:
            detail=action()
            cases.append(dict(name=name,passed=True,detail=detail))
        except Exception as error:cases.append(dict(name=name,passed=False,error=str(error)))
    native=c.NativeMMIO32(ROOT/'build/mmio32-host.dll')
    memory=(ctypes.c_uint32*1024)(*[0xa5a5a5a5]*1024)
    address=ctypes.addressof(memory)

    def CPU_native_call():
        native.write(address+4,0x12345678)
        assert native.read(address+4)==0x12345678 and memory[1]==0x12345678
        assert all(value==0xa5a5a5a5 for i,value in enumerate(memory) if i!=1)
        return dict(ordinary_memory_only=True,address_aligned=address%4==0,value=memory[1])
    check('real_ctypes_native_DLL_ordinary_memory_load_store',CPU_native_call)

    def alignment_rejections():
        original=bytes(memory)
        out=ctypes.c_uint32(0xdeadbeef)
        assert native.library.mmio32_write32(address+1,1)==22
        assert native.library.mmio32_write32(None,1)==22
        assert native.library.mmio32_read32(address+1,ctypes.byref(out))==22
        assert native.library.mmio32_read32(None,ctypes.byref(out))==22
        assert native.library.mmio32_read32(address,None)==22
        assert out.value==0xdeadbeef and original==bytes(memory)
        return dict(invalid_calls_rejected_without_memory_change=5)
    check('C_rejects_null_and_unaligned_addresses_before_access',alignment_rejections)

    def one_MMIO_call():
        events=Evidence()
        calls=[]
        def write(where,value):
            calls.append(dict(operation='write',address=where,value=value,
                              before=ctypes.c_uint32.from_address(where).value,
                              persisted_attempts=len(events.events)))
            native.write(where,value)
        def read(where):
            calls.append(dict(operation='read',address=where))
            return native.read(where)
        fake=SimpleNamespace(address=address,native=SimpleNamespace(write=write,read=read),
                             evidence=events,boot_id='CPU-only')
        c.runtime=lambda:'CPU-only'
        c.MMIO.write(fake,c.MON,1)
        assert len(calls)==1 and calls[0]['before']==0xa5a5a5a5 and calls[0]['persisted_attempts']==1
        assert memory[c.MON//4]==1
        assert c.MMIO.read(fake,c.MON)==1 and len(calls)==2
        return dict(native_write_calls=1,native_read_calls=1,write_value=1,prior_value=0xa5a5a5a5,
                    attempt_persisted_before_native_call=True)
    check('one_command_attempt_one_native_store_no_zero_prefill',one_MMIO_call)

    def zero_first_counterexample():
        buffer=bytearray(b'\xa5'*4)
        seen=[]
        class Value:
            def __index__(self):
                seen.append(bytes(buffer).hex())
                return 1
        struct.pack_into('<I',buffer,0,Value())  # CPU bytearray only, never an mmap.
        assert seen==['00000000'] and buffer.hex()=='01000000'
        return dict(Python=sys.version,ordinary_bytearray=True,initial='a5a5a5a5',
                    during_index=seen,final=buffer.hex(),MMIO=0)
    check('ordinary_buffer_struct_pack_into_zero_first_counterexample',zero_first_counterexample)

    def target_instructions():
        text=(ROOT/'build/aarch64-objdump.txt').read_text()
        def function(name):
            match=re.search(r'^[0-9a-f]+ <'+name+r'>:\n(.*?)(?=^[0-9a-f]+ <|\Z)',text,re.M|re.S)
            assert match,name+' symbol missing'
            return match[1]
        write=function('mmio32_write32')
        read=function('mmio32_read32')
        # GCC preserves the incoming device pointer x0 in x2 before reusing w0
        # for the integer return code. Check that actual compiled alias, rather
        # than requiring a particular argument register to remain unrenamed.
        assert re.search(r'\bmov\s+x2,\s*x0\b',write) and re.search(r'\bmov\s+x2,\s*x0\b',read)
        assert len(re.findall(r'\bstr\s+w\d+,\s*\[x2\]',write))==1
        assert len(re.findall(r'\bldr\s+w\d+,\s*\[x2\]',read))==1
        assert len(re.findall(r'\bstr\s+',write))==1
        assert not re.search(r'\b(strb|strh|stp|sturb|sturh)\b',write)
        assert write.count('dmb\tsy')==write.count('dsb\tsy')==1
        assert read.count('dmb\tsy')==read.count('dsb\tsy')==1
        return dict(AArch64_device_store_instructions=1,AArch64_device_load_instructions=1,
                    write_barriers=['dmb sy','dsb sy'],read_barriers=['dmb sy','dsb sy'],
                    note='CPU instruction shape; no observed AXI beat count is claimed.')
    check('actual_AArch64_library_has_one_device_STR_W_and_LDR_W',target_instructions)

    report=dict(CPU_ordinary_memory_only=True,board_access=False,SDK_loaded=False,
                total=len(cases),passed=sum(row['passed'] for row in cases),cases=cases)
    (ROOT/'build/mmio32-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    for row in cases:
        if not row['passed']:print(row)
    assert report['passed']==report['total']
    print('MMIO32_CPU_AND_DISASSEMBLY_TESTS',report['passed'],'/',report['total'],'NO_BOARD_PASS_CLAIM')


if __name__=='__main__':main()
