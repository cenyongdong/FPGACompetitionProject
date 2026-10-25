// Offline, bounded-memory verification of the actual PIWFUL3 archive. Repeated
// sources are compared with their first saved record, never substituted into it.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { FULL_BYTES, decodeFull } from './full_record.mjs';

export async function analyze(archive, catalogPath) {
    const catalog=JSON.parse(await fs.promises.readFile(catalogPath,'utf8'));
    if(!catalog.samples?.length)throw new Error('Missing source catalog');
    const file=await fs.promises.open(archive,'r'), first=new Map();
    const bytes=Buffer.alloc(FULL_BYTES),reference=Buffer.alloc(FULL_BYTES);
    let scanned=0,repeats=0,changed=0,session=null;
    const failures=[];
    async function read(target,position){
        let used=0;
        while(used<target.length){const result=await file.read(target,used,target.length-used,position+used);
            if(!result.bytesRead)throw new Error('Truncated complete archive');used+=result.bytesRead;}
    }
    try {
        const size=(await file.stat()).size,records=Math.floor(size/FULL_BYTES);
        if(size%FULL_BYTES)failures.push({kind:'partial_record',bytes:size%FULL_BYTES});
        for(let index=0;index<records;++index){
            await read(bytes,index*FULL_BYTES);
            try {
                const frame=decodeFull(bytes);
                session??=frame.session;
                if(frame.session!==session||frame.frame!==String(1000000+index)||frame.invocation!==String(index)||frame.sequence!==String(index+1))
                    throw new Error('Archive session/frame/invocation order differs');
                const source=catalog.samples[index%catalog.samples.length];
                const key=(source.split||'test')+':'+(source.payload_index??source.index??source.name);
                if(first.has(key)){
                    await read(reference,first.get(key)*FULL_BYTES);++repeats;
                    if(!bytes.subarray(384).equals(reference.subarray(384))){++changed;
                        if(failures.length<32)failures.push({kind:'repeated_source_values_differ',invocation:index,first_invocation:first.get(key),source:key});}
                }else first.set(key,index);
                ++scanned;
            }catch(error){if(failures.length<32)failures.push({kind:'invalid_complete_record',invocation:index,error:error.message});}
        }
        return {schema:'PIWFUL3/3',full_bytes:FULL_BYTES,archive_bytes:size,records,
            valid_records:scanned,unique_sources:first.size,repeated_sources:repeats,repeated_source_changes:changed,
            passed:scanned===records&&!changed&&size%FULL_BYTES===0&&records>0,failures,
            numerical_accuracy_accepted:false,reference:'first saved actual values of each simulated source; no late rereads or replacement'};
    }finally{await file.close();}
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
    const [archive,catalog,output]=process.argv.slice(2);
    if(!archive||!catalog||!output)throw new Error('archive catalog.json fresh-analysis.json required');
    const result=await analyze(archive,catalog);
    fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
    console.log(JSON.stringify(result));if(!result.passed)process.exitCode=1;
}
