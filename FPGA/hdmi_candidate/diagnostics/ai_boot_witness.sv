// Passive history from configuration, independent of ARM and PL/local reset.
// Persistent registers use configuration INIT only. Reprogramming starts a new
// history; a local reset clears only the published CSR snapshot.
module ai_boot_witness (
    input wire source_clk,csr_clk,csr_resetn,gp_reset,
    input wire source_freeze,csr_freeze,
    input wire [4:0] source_flags,
    input wire [127:0] ps_read,hdmi_read,
    output wire [607:0] held_words
);
    localparam [31:0] ABI=32'h42545201;
    reg [31:0] cycles=0,ps_ar_count=0,ps_r_count=0,hdmi_ar_count=0,hdmi_r_count=0;
    reg [7:0] cycle_wraps=0;
    reg wrap_overflow=0;
    reg [3:0] count_overflow=0;
    reg ps_ar_seen=0,ps_valid_seen=0,hdmi_ar_seen=0,valid_without_ar=0;
    reg ar_during_reset=0,ar_before_calibration=0,valid_during_reset=0;
    reg [2:0] first_valid_flags=0;
    reg [1:0] first_ar_flags=0;
    reg [31:0] first_ps_ar_address=0,first_ps_ar_pins=0;
    reg [31:0] first_ps_valid_pins=0,first_ps_valid_cycle=0;
    reg [31:0] first_hdmi_ar_address=0,first_hdmi_ar_cycle=0;
    reg [383:0] source_snapshot=0;
    wire ps_ar=ps_read[60] && ps_read[61];
    wire ps_r=ps_read[62] && ps_read[63];
    wire hdmi_ar=hdmi_read[60] && hdmi_read[61];
    wire hdmi_r=hdmi_read[62] && hdmi_read[63];
    wire reset_released=source_flags[3] && !source_flags[2];
    wire ready_path=reset_released && source_flags[0] && !source_flags[1];
    function [31:0] pins(input [127:0] b);
        pins={4'd0,b[72],b[70+:2],b[64+:6],b[45+:2],b[42+:3],
              b[38+:4],b[32+:6],b[60+:4]};
    endfunction
    wire [31:0] history_flags={cycle_wraps,first_ar_flags,1'b0,first_valid_flags,
        wrap_overflow,count_overflow,source_flags,1'b0,
        valid_during_reset,ar_before_calibration,ar_during_reset,
        valid_without_ar,hdmi_ar_seen,ps_valid_seen,ps_ar_seen};
    always @(posedge source_clk) begin
        cycles<=cycles+1'b1;
        if(&cycles) begin
            if(&cycle_wraps)wrap_overflow<=1;
            else cycle_wraps<=cycle_wraps+1'b1;
        end
        if(ps_ar) begin
            ps_ar_count<=ps_ar_count+1'b1;
            if(&ps_ar_count)count_overflow[0]<=1;
            if(!ps_ar_seen) begin
                ps_ar_seen<=1;first_ps_ar_address<=ps_read[31:0];
                first_ps_ar_pins<=pins(ps_read);
                first_ar_flags<={source_flags[0],reset_released};
            end
        end
        if(ps_r) begin
            ps_r_count<=ps_r_count+1'b1;
            if(&ps_r_count)count_overflow[1]<=1;
        end
        if(hdmi_ar) begin
            hdmi_ar_count<=hdmi_ar_count+1'b1;
            if(&hdmi_ar_count)count_overflow[2]<=1;
            if(!hdmi_ar_seen) begin
                hdmi_ar_seen<=1;first_hdmi_ar_address<=hdmi_read[31:0];
                first_hdmi_ar_cycle<=cycles;
            end
        end
        if(hdmi_r) begin
            hdmi_r_count<=hdmi_r_count+1'b1;
            if(&hdmi_r_count)count_overflow[3]<=1;
        end
        // Raw handshake conditions during reset are evidence, not proof that
        // the receiving endpoint accepted a protocol-valid transaction.
        if((ps_ar || hdmi_ar) && !reset_released)ar_during_reset<=1;
        if((ps_ar || hdmi_ar) && !source_flags[0])ar_before_calibration<=1;
        if(ps_read[62] && !reset_released)valid_during_reset<=1;
        // Ignore undefined reset-time RVALID for the first healthy-path sample.
        if(ps_read[62] && ready_path && !ps_valid_seen) begin
            ps_valid_seen<=1;first_ps_valid_pins<=pins(ps_read);
            first_ps_valid_cycle<=cycles;
            first_valid_flags<={source_flags[0],source_flags[3],source_flags[2]};
            if(ps_ar_count==0 && !ps_ar)valid_without_ar<=1;
        end
        if(source_freeze) begin
            source_snapshot[0*32+:32]<=history_flags;
            source_snapshot[1*32+:32]<=cycles;
            source_snapshot[2*32+:32]<=ps_ar_count;
            source_snapshot[3*32+:32]<=ps_r_count;
            source_snapshot[4*32+:32]<=hdmi_ar_count;
            source_snapshot[5*32+:32]<=hdmi_r_count;
            source_snapshot[6*32+:32]<=first_ps_ar_address;
            source_snapshot[7*32+:32]<=first_ps_ar_pins;
            source_snapshot[8*32+:32]<=first_ps_valid_pins;
            source_snapshot[9*32+:32]<=first_ps_valid_cycle;
            source_snapshot[10*32+:32]<=first_hdmi_ar_address;
            source_snapshot[11*32+:32]<=first_hdmi_ar_cycle;
        end
    end

    // GP runs independently of the MIG-derived HP clock. These counters can
    // witness HP reset assertion even when HP/source clocks are stopped.
    (* ASYNC_REG="TRUE",SHREG_EXTRACT="NO" *) reg [4:0] flags_meta=0,flags_sync=0;
    reg [2:0] gp_sample_valid=0;
    reg gp_reset_previous=0,hp_reset_previous=1;
    reg [31:0] gp_cycles=0,gp_reset_edges=0,hp_reset_edges=0;
    reg [31:0] gp_reset_cycles=0,hp_reset_cycles=0;
    reg [7:0] gp_wraps=0;
    reg [4:0] gp_overflow=0;
    reg gp_reset_seen=0,hp_reset_seen=0;
    wire [31:0] gp_flags={gp_wraps,7'd0,gp_overflow[4],2'd0,
        gp_reset_seen,hp_reset_seen,gp_overflow[3:0],1'b1,gp_reset,
        flags_sync,1'b0};
    always @(posedge csr_clk) begin
        flags_meta<=source_flags;flags_sync<=flags_meta;
        gp_sample_valid<={gp_sample_valid[1:0],1'b1};
        gp_cycles<=gp_cycles+1'b1;
        if(&gp_cycles) begin
            if(&gp_wraps)gp_overflow[4]<=1;
            else gp_wraps<=gp_wraps+1'b1;
        end
        if(gp_sample_valid[2]) begin
            gp_reset_previous<=gp_reset;hp_reset_previous<=flags_sync[3];
            if(gp_reset) begin
                gp_reset_seen<=1;gp_reset_cycles<=gp_reset_cycles+1'b1;
                if(&gp_reset_cycles)gp_overflow[2]<=1;
            end
            if(!flags_sync[3]) begin
                hp_reset_seen<=1;hp_reset_cycles<=hp_reset_cycles+1'b1;
                if(&hp_reset_cycles)gp_overflow[3]<=1;
            end
            if(gp_reset && !gp_reset_previous) begin
                gp_reset_edges<=gp_reset_edges+1'b1;
                if(&gp_reset_edges)gp_overflow[0]<=1;
            end
            if(!flags_sync[3] && hp_reset_previous) begin
                hp_reset_edges<=hp_reset_edges+1'b1;
                if(&hp_reset_edges)gp_overflow[1]<=1;
            end
        end
    end
    reg [575:0] csr_snapshot;
    assign held_words={csr_snapshot,ABI};
    always @(posedge csr_clk or negedge csr_resetn) begin
        if(!csr_resetn)csr_snapshot<=0;
        else if(csr_freeze) begin
            csr_snapshot[0+:384]<=source_snapshot;
            csr_snapshot[384+:32]<=gp_reset_edges;
            csr_snapshot[416+:32]<=hp_reset_edges;
            csr_snapshot[448+:32]<=gp_cycles;
            csr_snapshot[480+:32]<=gp_reset_cycles;
            csr_snapshot[512+:32]<=hp_reset_cycles;
            csr_snapshot[544+:32]<=gp_flags;
        end
    end
endmodule
