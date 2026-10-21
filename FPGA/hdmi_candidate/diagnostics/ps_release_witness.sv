// Configuration-lifetime passive recorder. No functional reset/AXI outputs.
// The first FREEZE seals the GP log; CSR reset only hides publication.
// HP counts are raw handshakes, including reset-time pin combinations.
module ps_release_witness #(
    parameter integer EVENT_DEPTH=16
)(
    input wire source_clk,csr_clk,csr_resetn,source_freeze,csr_freeze,
    input wire [19:0] levels,
    input wire [127:0] ps_read,hdmi_read,
    input wire [5:0] legacy_write,ps_write,
    input wire [31:0] ps_awaddr,
    mna_gp_ww_itf.slave csr
);
    localparam [31:0] ABI=32'h50534c01;
    reg [63:0] hp_cycles=0;
    reg [7:0] hp_divider=0;
    wire [7:0] handshakes={ps_write[4]&ps_write[5],ps_write[2]&ps_write[3],
        ps_write[0]&ps_write[1],legacy_write[4]&legacy_write[5],
        legacy_write[2]&legacy_write[3],legacy_write[0]&legacy_write[1],
        ps_read[62]&ps_read[63],ps_read[60]&ps_read[61]};
    reg [31:0] counts[0:7];
    reg [7:0] count_overflow=0;
    reg [3:0] first_seen=0;
    reg [63:0] first_ar=0,first_r=0,first_write=0;
    reg [31:0] first_r_pins=0,first_aw_address=0;
    reg [19:0] first_r_levels=0;
    reg [63:0] first_ready_r=0;
    reg [31:0] first_ready_r_pins=0;
    reg [1023:0] source_snapshot=0,csr_source_snapshot=0;
    integer i;
    initial for(integer k=0;k<8;k=k+1)counts[k]=0;
    always @(posedge source_clk) begin
        hp_cycles[31:0]<=hp_cycles[31:0]+1'b1;
        if(&hp_cycles[31:0])hp_cycles[63:32]<=hp_cycles[63:32]+1'b1;
        hp_divider<=hp_divider+1'b1;
        for(i=0;i<8;i=i+1)if(handshakes[i]) begin
            counts[i]<=counts[i]+1'b1;
            if(&counts[i])count_overflow[i]<=1;
        end
        if(handshakes[0] && !first_seen[0])begin first_ar<=hp_cycles;first_seen[0]<=1;end
        if(ps_read[62] && !first_seen[1])begin
            first_r<=hp_cycles;first_seen[1]<=1;
            first_r_pins<={23'd0,ps_read[64+:9]};first_r_levels<=levels;
        end
        if((|handshakes[7:2]) && !first_seen[2])begin
            first_write<=hp_cycles;first_seen[2]<=1;
            first_aw_address<=ps_awaddr;
        end
        if(ps_read[62] && levels[1] && !levels[3] && !levels[5] && levels[6] && !first_seen[3])begin
            first_seen[3]<=1;first_ready_r<=hp_cycles;
            first_ready_r_pins<={23'd0,ps_read[64+:9]};
        end
        if(source_freeze)begin
            source_snapshot<=0;
            source_snapshot[0+:64]<=hp_cycles;
            source_snapshot[64+:32]<={20'd0,count_overflow,first_seen};
            for(i=0;i<8;i=i+1)source_snapshot[(4+i)*32+:32]<=counts[i];
            source_snapshot[12*32+:64]<=first_ar;
            source_snapshot[14*32+:64]<=first_r;
            source_snapshot[16*32+:64]<=first_write;
            source_snapshot[18*32+:32]<=first_r_pins;
            source_snapshot[19*32+:32]<={12'd0,first_r_levels};
            source_snapshot[20*32+:32]<=first_aw_address;
            source_snapshot[21*32+:64]<=first_ready_r;
            source_snapshot[23*32+:32]<=first_ready_r_pins;
        end
    end

    (* ASYNC_REG="TRUE",SHREG_EXTRACT="NO" *) reg [19:0] levels_meta=0,levels_sync=0;
    (* ASYNC_REG="TRUE",SHREG_EXTRACT="NO" *) reg beat_meta=0,beat_sync=0;
    reg beat_previous=0,hp_seen=0;
    reg [7:0] beat_age=255;
    reg [63:0] last_hp_beat=0;
    reg [2:0] valid_pipe=0;
    reg [63:0] gp_cycles=0,sealed_cycle=0;
    reg [19:0] initial_levels=0,last_levels=0;
    reg [63:0] first_time[0:7];
    reg [7:0] gp_seen=0;
    reg [63:0] last_ps_release=0,last_pl_release=0;
    reg [4:0] event_count=0;
    reg overflow=0,sealed=0;
    reg [95:0] events[0:EVENT_DEPTH-1];
    wire [19:0] sampled={levels_sync[19:8],hp_seen && !(&beat_age),levels_sync[6:0]};
    wire [7:0] targets={|sampled[17:12],sampled[7],sampled[10],sampled[8],
        sampled[11],sampled[9],sampled[1],sampled[0]};
    initial for(integer k=0;k<8;k=k+1)first_time[k]=0;
    always @(posedge csr_clk)begin
        gp_cycles[31:0]<=gp_cycles[31:0]+1'b1;
        if(&gp_cycles[31:0])gp_cycles[63:32]<=gp_cycles[63:32]+1'b1;
        levels_meta<=levels;levels_sync<=levels_meta;
        beat_meta<=hp_divider[7];beat_sync<=beat_meta;beat_previous<=beat_sync;
        if(!sealed)begin
            if(beat_sync!=beat_previous)begin
                hp_seen<=1;beat_age<=0;last_hp_beat<=gp_cycles;
            end else if(!(&beat_age))beat_age<=beat_age+1'b1;
        end
        valid_pipe<={valid_pipe[1:0],1'b1};
        if(!sealed && valid_pipe[2])begin
            if(!gp_seen[7] && event_count==0)initial_levels<=sampled;
            for(integer k=0;k<8;k=k+1)if(targets[k] && !gp_seen[k])begin
                gp_seen[k]<=1;first_time[k]<=gp_cycles;
            end
            if(sampled[0] && !last_levels[0])last_ps_release<=gp_cycles;
            if(sampled[1] && !last_levels[1])last_pl_release<=gp_cycles;
            if(event_count==0 || sampled!=last_levels)begin
                if(event_count<EVENT_DEPTH)begin
                    events[event_count]<={12'd0,sampled,gp_cycles};
                    event_count<=event_count+1'b1;
                end else overflow<=1;
            end
            last_levels<=sampled;
        end
        if(csr_freeze && !sealed)begin sealed<=1;sealed_cycle<=gp_cycles;end
    end

    reg published=0,read_valid;
    reg [31:0] publication_count=0,read_value,selected;
    wire [6:0] index=csr.araddr[8:2];
    // In the event bank bit6 is the fixed base 64. Keep division/modulo
    // six bits wide; (index-64)/3 otherwise expands to a 32-bit divider.
    wire [5:0] event_offset=index[5:0];
    wire [5:0] event_slot=event_offset/6'd3;
    wire [1:0] event_lane=event_offset%6'd3;
    wire [2:0] first_slot=index[3:1]-3'd4;
    assign csr.awwready=csr_resetn; // Writes are ignored, including START/reset.
    assign csr.arready=csr_resetn && (!read_valid || csr.rready);
    assign csr.rvalid=read_valid;
    assign csr.rdata=read_value;
    always @* begin
        selected=0;
        case(index)
            0:selected=ABI;
            1:selected={21'd0,gp_seen,overflow,sealed,published};
            2:selected=sealed_cycle[31:0];3:selected=sealed_cycle[63:32];
            4:selected={12'd0,initial_levels};5:selected={12'd0,last_levels};
            6:selected={27'd0,event_count};7:selected=publication_count;
            24:selected=last_ps_release[31:0];25:selected=last_ps_release[63:32];
            26:selected=last_pl_release[31:0];27:selected=last_pl_release[63:32];
            28:selected=last_hp_beat[31:0];29:selected=last_hp_beat[63:32];
            30:selected={24'd0,beat_age};
            default:begin
                if(index>=8 && index<24)
                    selected=index[0] ? first_time[first_slot][63:32] : first_time[first_slot][31:0];
                else if(index>=32 && index<64)selected=csr_source_snapshot[32*index[4:0]+:32];
                else if(index>=64 && index<64+3*EVENT_DEPTH && event_slot<event_count)
                    case(event_lane)
                        0:selected=events[event_slot][31:0];
                        1:selected=events[event_slot][63:32];
                        2:selected=events[event_slot][95:64];
                        default:selected=0;
                    endcase
            end
        endcase
        if(!published && index!=0 && index!=1)selected=0;
        if(csr.araddr[1:0]!=0)selected=32'hbad00001;
    end
    always @(posedge csr_clk or negedge csr_resetn)begin
        if(!csr_resetn)begin
            published<=0;read_valid<=0;read_value<=0;csr_source_snapshot<=0;
        end else begin
            if(csr_freeze)begin published<=1;csr_source_snapshot<=source_snapshot;end
            if(csr.arvalid && csr.arready)begin read_valid<=1;read_value<=selected;end
            else if(csr.rready)read_valid<=0;
        end
    end
    always @(posedge csr_clk)if(csr_freeze)publication_count<=publication_count+1'b1;
endmodule
