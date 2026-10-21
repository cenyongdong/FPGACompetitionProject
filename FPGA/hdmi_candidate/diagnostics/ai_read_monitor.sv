// Passive six-boundary read-path observation. Outputs only serve the CSR bus.
// ARM/FREEZE each have their own one-bit toggle request/acknowledgement CDC.
module ai_read_monitor #(parameter integer BOOT_WITNESS=0) (
    input wire source_clk,input wire csr_clk,input wire resetn,
    input wire [767:0] channels,input wire [4:0] source_flags,
    input wire witness_gp_reset,
    mna_gp_ww_itf.slave csr
);
    localparam [31:0] ABI=32'h41495201;
    localparam integer WORDS=104;
    (* ASYNC_REG="TRUE" *) reg [2:0] source_release,csr_release;
    always @(posedge source_clk or negedge resetn)
        if(!resetn)source_release<=0;
        else source_release<={source_release[1:0],1'b1};
    always @(posedge csr_clk or negedge resetn)
        if(!resetn)csr_release<=0;
        else csr_release<={csr_release[1:0],1'b1};
    wire source_resetn=source_release[2],csr_resetn=csr_release[2];

    reg arm_request_toggle,freeze_request_toggle;
    reg arm_ack_toggle,freeze_ack_toggle;
    (* ASYNC_REG="TRUE" *) reg [1:0] arm_request_sync,freeze_request_sync;
    (* ASYNC_REG="TRUE" *) reg [1:0] arm_ack_sync,freeze_ack_sync;
    reg source_active;
    reg [31:0] live_words[0:WORDS-1];
    reg [32*WORDS-1:0] source_snapshot;
    integer i,ch,base;
    always @(posedge source_clk or negedge source_resetn) begin
        if(!source_resetn) begin
            arm_request_sync<=0;freeze_request_sync<=0;
            arm_ack_toggle<=0;freeze_ack_toggle<=0;
            source_active<=0;source_snapshot<=0;
            for(i=0;i<WORDS;i=i+1)live_words[i]<=0;
            live_words[0]<=ABI;
        end else begin
            arm_request_sync<={arm_request_sync[0],arm_request_toggle};
            freeze_request_sync<={freeze_request_sync[0],freeze_request_toggle};
            if(arm_request_sync[1]!=arm_ack_toggle) begin
                // Accepted ARM starts a new diagnostic epoch. No functional
                // state/reset, handshake, memory or data-path signal is driven.
                for(i=0;i<WORDS;i=i+1)live_words[i]<=0;
                live_words[0]<=ABI;
                source_snapshot<=0;source_active<=1;
                arm_ack_toggle<=arm_request_sync[1];
            end else if(freeze_request_sync[1]!=freeze_ack_toggle) begin
                // The FREEZE edge itself is excluded: the snapshot is exactly
                // the diagnostic state after the preceding active source edge.
                for(i=0;i<WORDS;i=i+1)
                    source_snapshot[32*i+:32]<=live_words[i];
                source_active<=0;
                freeze_ack_toggle<=freeze_request_sync[1];
            end else if(source_active) begin
                live_words[1]<=live_words[1]+1'b1;
                live_words[2]<={27'd0,source_flags};
                if(source_flags[2] || !source_flags[3])live_words[3]<=live_words[3]+1'b1;
                for(ch=0;ch<6;ch=ch+1) begin
                    base=8+16*ch;
                    // Channel flags: ARVALID60, ARREADY61, RVALID62, RREADY63.
                    if(channels[128*ch+60] && channels[128*ch+61]) begin
                        live_words[base+0]<=live_words[base+0]+1'b1;
                        live_words[base+8]<=channels[128*ch+:32];
                        live_words[base+9]<={4'd0,channels[128*ch+32+:28]};
                        live_words[base+15]<=live_words[base+15]+{28'd0,channels[128*ch+38+:4]}+32'd1;
                    end
                    if(channels[128*ch+62] && channels[128*ch+63]) begin
                        live_words[base+1]<=live_words[base+1]+1'b1;
                        if(channels[128*ch+72])live_words[base+2]<=live_words[base+2]+1'b1;
                        live_words[base+10]<={23'd0,channels[128*ch+64+:9]};
                        if(channels[128*ch+70+:2]!=0) begin
                            live_words[base+3]<=live_words[base+3]+1'b1;
                            if(!live_words[base+12][31]) begin
                                live_words[base+12]<={1'b1,22'd0,channels[128*ch+64+:9]};
                                live_words[base+13]<=live_words[1];
                            end
                        end
                    end
                    if(channels[128*ch+60] && !channels[128*ch+61])
                        live_words[base+4]<=live_words[base+4]+1'b1;
                    if(channels[128*ch+62] && !channels[128*ch+63])
                        live_words[base+5]<=live_words[base+5]+1'b1;
                    if(channels[128*ch+60])live_words[base+6]<=live_words[base+6]+1'b1;
                    if(channels[128*ch+62])live_words[base+7]<=live_words[base+7]+1'b1;
                    // Current pins, not an accepted/pending transaction ledger.
                    live_words[base+11]<={4'd0,channels[128*ch+72],channels[128*ch+70+:2],
                        channels[128*ch+64+:6],channels[128*ch+45+:2],channels[128*ch+42+:3],
                        channels[128*ch+38+:4],channels[128*ch+32+:6],channels[128*ch+60+:4]};
                    if((channels[128*ch+60] && channels[128*ch+61]) ||
                       (channels[128*ch+62] && channels[128*ch+63]))
                        live_words[base+14]<=live_words[1];
                end
            end
        end
    end

    reg [32*WORDS-1:0] csr_snapshot;
    reg [31:0] request_sequence,response_sequence;
    reg busy,command_error,pending_freeze,csr_armed,read_valid;
    reg [31:0] selected,read_value;
    wire [8:0] write_offset=csr.awwaddr[8:0];
    wire [8:0] read_offset=csr.araddr[8:0];
    wire [607:0] boot_words;
    generate if(BOOT_WITNESS) begin:boot_history
        ai_boot_witness witness(
            .source_clk(source_clk),.csr_clk(csr_clk),.csr_resetn(csr_resetn),
            .gp_reset(witness_gp_reset),.source_flags(source_flags),
            .ps_read(channels[640+:128]),.hdmi_read(channels[512+:128]),
            .source_freeze(source_resetn && arm_request_sync[1]==arm_ack_toggle &&
                freeze_request_sync[1]!=freeze_ack_toggle),
            .csr_freeze(busy && pending_freeze &&
                freeze_ack_sync[1]==freeze_request_toggle),.held_words(boot_words));
    end else begin:no_boot_history
        assign boot_words=0;
    end endgenerate
    assign csr.awwready=csr_resetn;
    assign csr.arready=csr_resetn && (!read_valid || csr.rready);
    assign csr.rdata=read_value;
    assign csr.rvalid=read_valid;
    always @* begin
        selected=0;
        case(read_offset)
            9'h000:selected={30'd0,command_error,busy};
            9'h004:selected=ABI;
            9'h008:selected=request_sequence;
            9'h00c:selected=response_sequence;
            9'h010:selected=WORDS;
            default:begin
                if(read_offset>=9'h040 && read_offset<=9'h1dc && read_offset[1:0]==0)
                    selected=csr_snapshot[32*((read_offset-9'h040)>>2)+:32];
                else if(read_offset>=9'h014 && read_offset<=9'h03c && read_offset[1:0]==0)
                    selected=boot_words[32*((read_offset-9'h014)>>2)+:32];
                else if(read_offset>=9'h1e0 && read_offset<=9'h1fc && read_offset[1:0]==0)
                    selected=boot_words[32*(11+((read_offset-9'h1e0)>>2))+:32];
            end
        endcase
        if(read_offset[1:0]!=0)selected=32'hbad00001;
    end
    always @(posedge csr_clk or negedge csr_resetn) begin
        if(!csr_resetn) begin
            arm_ack_sync<=0;freeze_ack_sync<=0;
            arm_request_toggle<=0;freeze_request_toggle<=0;
            request_sequence<=0;response_sequence<=0;
            busy<=0;command_error<=0;pending_freeze<=0;csr_armed<=0;
            read_valid<=0;read_value<=0;csr_snapshot<=0;
        end else begin
            arm_ack_sync<={arm_ack_sync[0],arm_ack_toggle};
            freeze_ack_sync<={freeze_ack_sync[0],freeze_ack_toggle};
            if(busy && ((!pending_freeze && arm_ack_sync[1]==arm_request_toggle) ||
                        (pending_freeze && freeze_ack_sync[1]==freeze_request_toggle))) begin
                if(pending_freeze) begin
                    // The held bus preceded the two-stage ACK. It remains held
                    // until a later accepted ARM; external timing must bind it.
                    csr_snapshot<=source_snapshot;csr_armed<=0;
                end else begin
                    csr_snapshot<=0;csr_armed<=1;
                end
                response_sequence<=request_sequence;busy<=0;
            end
            if(csr.awwvalid && csr.awwready) begin
                if(write_offset==0 && csr.awwdata==1 && !busy && !csr_armed) begin
                    arm_request_toggle<=!arm_request_toggle;pending_freeze<=0;
                    request_sequence<=request_sequence+1'b1;busy<=1;
                end else if(write_offset==0 && csr.awwdata==2 && !busy && csr_armed) begin
                    freeze_request_toggle<=!freeze_request_toggle;pending_freeze<=1;
                    request_sequence<=request_sequence+1'b1;busy<=1;
                end else command_error<=1;
            end
            if(csr.arvalid && csr.arready)begin read_valid<=1;read_value<=selected;end
            else if(csr.rready)read_valid<=0;
        end
    end
endmodule
