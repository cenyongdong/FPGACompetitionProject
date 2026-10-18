// Passive event observation. Only snapshot commands cross into the source domain.
// No output drives the AI, DDR, reset or HDMI data paths.
module ai_event_monitor (
    input wire source_clk,input wire csr_clk,input wire resetn,
    input wire [15:0] events,
    input wire [7:0] sample_update,input wire [255:0] sample_data,
    mna_gp_ww_itf.slave csr
);
    (* ASYNC_REG="TRUE" *) reg [2:0] source_release,csr_release;
    always @(posedge source_clk or negedge resetn)
        if(!resetn) source_release<=0;
        else source_release<={source_release[1:0],1'b1};
    always @(posedge csr_clk or negedge resetn)
        if(!resetn) csr_release<=0;
        else csr_release<={csr_release[1:0],1'b1};
    wire source_resetn=source_release[2],csr_resetn=csr_release[2];

    reg [31:0] counters[0:15];
    reg [31:0] samples[0:7];
    reg [767:0] source_snapshot;
    reg request_toggle,ack_toggle;
    (* ASYNC_REG="TRUE" *) reg [1:0] request_sync,ack_sync;
    integer i;
    always @(posedge source_clk or negedge source_resetn) begin
        if(!source_resetn) begin
            request_sync<=0;ack_toggle<=0;source_snapshot<=0;
            for(i=0;i<16;i=i+1)counters[i]<=0;
            for(i=0;i<8;i=i+1)samples[i]<=0;
        end else begin
            request_sync<={request_sync[0],request_toggle};
            for(i=0;i<16;i=i+1)if(events[i])counters[i]<=counters[i]+1'b1;
            for(i=0;i<8;i=i+1)if(sample_update[i])samples[i]<=sample_data[32*i+:32];
            if(request_sync[1]!=ack_toggle) begin
                for(i=0;i<16;i=i+1)source_snapshot[32*i+:32]<=counters[i];
                for(i=0;i<8;i=i+1)source_snapshot[32*(i+16)+:32]<=samples[i];
                ack_toggle<=request_sync[1];
            end
        end
    end

    reg [767:0] csr_snapshot;
    reg [31:0] request_sequence,response_sequence;
    reg busy,command_error,read_valid;
    reg [31:0] read_value,selected;
    wire [7:0] write_offset=csr.awwaddr[7:0];
    wire [7:0] read_offset=csr.araddr[7:0];
    assign csr.awwready=csr_resetn;
    assign csr.arready=csr_resetn && (!read_valid || csr.rready);
    assign csr.rdata=read_value;
    assign csr.rvalid=read_valid;
    always @* begin
        selected=0;
        case(read_offset)
            8'h00:selected={30'd0,command_error,busy};
            8'h04:selected=32'h41494401;
            8'h08:selected=request_sequence;
            8'h0c:selected=response_sequence;
            8'h10:selected=24;
            default:if(read_offset>=8'h40 && read_offset<=8'h9c && read_offset[1:0]==0)
                selected=csr_snapshot[32*((read_offset-8'h40)>>2)+:32];
        endcase
        if(read_offset[1:0]!=0)selected=32'hbad00001;
    end
    always @(posedge csr_clk or negedge csr_resetn) begin
        if(!csr_resetn) begin
            ack_sync<=0;request_toggle<=0;request_sequence<=0;response_sequence<=0;
            busy<=0;command_error<=0;read_valid<=0;read_value<=0;csr_snapshot<=0;
        end else begin
            ack_sync<={ack_sync[0],ack_toggle};
            if(busy && ack_sync[1]==request_toggle) begin
                // source_snapshot was held before ack traversed both stages;
                // it remains held until a later, explicitly accepted request.
                csr_snapshot<=source_snapshot;
                response_sequence<=request_sequence;busy<=0;
            end
            if(csr.awwvalid && csr.awwready) begin
                if(write_offset==0 && csr.awwdata==1 && !busy) begin
                    request_sequence<=request_sequence+1'b1;
                    request_toggle<=!request_toggle;busy<=1;
                end else command_error<=1;
            end
            if(csr.arvalid && csr.arready)begin read_valid<=1;read_value<=selected;end
            else if(csr.rready)read_valid<=0;
        end
    end
endmodule
