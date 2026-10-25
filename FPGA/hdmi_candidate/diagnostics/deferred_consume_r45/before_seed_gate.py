"""Classify one untouched r45 startup; never authorizes functionality."""
RECOMMEND={92,93,95};KNOWN={58,59,61}

def evaluate(before,trace,protocol):
    result=dict(eligible=False,continue_allowed=False,classification='unsafe_or_inconclusive',
                boot_id=before.get('boot_id'),PS_AR=None,PS_R=None,reasons=[])
    def need(ok,msg):
        if not ok:raise ValueError(msg)
    try:
        identity=before['boot_id']
        need(before['valid'] and not before['overflow'] and trace['boot_id']==protocol['boot_id']==identity,'Invalid or mixed boot evidence')
        need(all(before[k]==0 for k in ('SDK','DMA','HDMI_START')),'Functional traffic already attempted')
        c=before['control'];d=before['drain'];life=before['counts_lifetime'];levels=before['levels']
        result.update(PS_AR=life['PS']['AR'],PS_R=life['PS']['R'])
        need(c['request']==c['response'] and not c['error'] and not c['arm_used'] and not c['arm_issued'] and not c['rearm_used'],'Control already used, pending or faulty')
        need(d['state']==d['beats']==d['HP_cycles']==0,'Consumer not untouched WAIT; request collision or activity occurred')
        need(levels['PS_HP2_resetn'] and levels['PL_HP2_resetn'] and not levels['HP_reset'],'Current reset boundary not ready')
        need(before['first_AR_HP_cycle'] is None and life['PS']['AR']==life['S01']['AR']==0 and life['S01']['R']==0,'Startup AR or S01 accepted return exists')
        need(all(v==0 for v in life['writes'].values()),'Lifetime write activity')
        need(all(x['AR']==x['ARVALID_cycles']==x['non_OKAY']==0 for x in before['counts_epoch'].values()),'Requests/error in observed epoch')
        need(before['counts_epoch']['HC2']['R']==0 and not levels['HC2_RVALID'],'HC2 return activity')
        flags=protocol['live_flags']
        need(all(flags[k] for k in ('PS_HP2_resetn','PC_system_resetn','PC_checker_ready','PC_seen_reset_low')),'Native checker reset coverage incomplete')
        live=c['full_PC_status'];bits={i for i in range(160) if live>>i&1}
        need(bits <= RECOMMEND|KNOWN,'Unknown native mandatory/capacity status')
        banks=trace['banks'];need(len(banks)==2 and not banks[1]['published'] and not banks[1].get('fired',False),'Consumer capture fired before explicit command')
        if before['first_RVALID_HP_cycle'] is None and life['PS']['R']==0 and not banks[0]['published']:
            need(not protocol['published'] and not protocol['fired'] and not(bits&KNOWN),'Native abnormality already recorded')
            need(not levels['PS_RVALID'] and not levels['S01_RVALID'],'Current return exists without historical first event')
            result.update(classification='healthy_no_target',continue_allowed=True,reasons=['Untouched WAIT, no lifetime PS/S01 AR/R or write activity, no first RVALID or mandatory native error.'])
            return result
        need(0<life['PS']['R']<256 and levels['PS_RVALID'] and levels['S01_RVALID'],'Known pending return absent or excessive')
        need(before['pins']['PS']['RID']==0x20 and before['pins']['PS']['RRESP']==0 and before['pins']['S01']['RID']==0 and before['pins']['S01']['RRESP']==0 and not before['pins']['S01']['RREADY'],'Unexpected current pending response')
        bank=banks[0];need(bank['published'] and bank['count']==len(bank['rows'])==128 and bank['trigger_index']==32,'First RVALID window incomplete')
        rows=bank['rows'];need(all(b['HP_cycle']==a['HP_cycle']+1 for a,b in zip(rows,rows[1:])),'First RVALID samples nonconsecutive')
        need(rows[32]['HP_cycle']==bank['trigger_cycle']==before['first_RVALID_HP_cycle'] and not rows[31]['PS_RVALID'] and rows[32]['PS_RVALID'],'First RVALID witness differs')
        for row in rows:
            need(not any(row[k+'_ARVALID'] for k in ('PS','S01','HC2')),'ARVALID in startup window')
            need(not any(row[k+'_AWVALID'] or row[k+'_WVALID'] or row[k+'_BVALID'] for k in ('PS','S01')),'Write in startup window')
            need(not(row['HC2_RVALID'] and row['HC2_RREADY']),'HC2 accepted startup return')
            need(row['drain_state']==0 and not row['S01_RREADY'],'Consumer was active before ARM')
            for channel,rid in (('PS',0x20),('S01',0)):
                need(not row[channel+'_RVALID'] or (row[channel+'_RID']==rid and row[channel+'_RRESP']==0),'Visible response ID/error differs')
        from consume_gate import _native
        actual=_native(protocol);need(bool(actual&KNOWN) and actual<=KNOWN|RECOMMEND,'Known native boundary not established')
        result.update(classification='known_unmatched_return',eligible=True,native_check_bits=sorted(actual),
                      reasons=['Same-boot original first RVALID/native error preserved; no lifetime AR/write, no prior S01 acceptance, no ARM; bounded diagnostic may be attempted once.'])
    except (KeyError,TypeError,ValueError,IndexError) as error:
        result['reasons']=[str(error)]
    return result
