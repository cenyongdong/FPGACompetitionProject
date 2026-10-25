import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { analyze } from '../analyze.mjs';
import { POSE_OFFSET } from '../full_record.mjs';
import { record } from './fixtures.mjs';

test('offline 180 archive checks repeated first values and rejects partial/changed results',async()=>{
    const root=fs.mkdtempSync(path.join(os.tmpdir(),'pose180-archive-'));
    try{
        const archive=path.join(root,'actual.full'),catalog=path.join(root,'catalog.json');
        fs.writeFileSync(catalog,JSON.stringify({samples:[{split:'test',index:0,name:'synthetic'}]}));
        const first=record({index:0}),second=record({index:1});
        fs.writeFileSync(archive,Buffer.concat([first,second]));
        let result=await analyze(archive,catalog);
        assert.equal(result.passed,true);assert.equal(result.valid_records,2);
        assert.equal(result.unique_sources,1);assert.equal(result.repeated_sources,1);
        second.writeFloatLE(1.25,POSE_OFFSET); // finite, unselected candidate; parser alone cannot reject it.
        fs.writeFileSync(archive,Buffer.concat([first,second]));
        result=await analyze(archive,catalog);
        assert.equal(result.passed,false);assert.equal(result.repeated_source_changes,1);
        assert.equal(fs.readFileSync(archive).readFloatLE(first.length+POSE_OFFSET),1.25);
        fs.writeFileSync(archive,first.subarray(0,first.length-1));
        result=await analyze(archive,catalog);assert.equal(result.passed,false);
        assert.equal(result.failures[0].kind,'partial_record');
    }finally{fs.rmSync(root,{recursive:true,force:true});}
});
