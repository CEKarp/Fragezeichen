`timescale 1ns/1ps
// cgp_alu: Cartesian Genetic Programming DUT
// 11 Knoten, jeder berechnet 1 Bit. Genom: 11 x 10 = 110 Bit.
//   Bit 0-1:   Funktion (AND, OR, XOR, NAND)
//   Bit 2-5:   Selector In1
//   Bit 6-9:   Selector In2
// Quellen: 0..2 = A[0..2], 3..5 = B[0..2], 6..(6+i-1) = k0..k{i-1}
// Ausgang: k10
module cgp_alu (
    input  wire        CLK, RST_N,
    input  wire [3:0]  DIN,
    input  wire        DIN_V, DIN_LAST,
    input  wire        FB_OK, FB_ERR,
    input  wire [127:0] GENOME,
    output reg  [3:0]  DOUT,
    output reg         DOUT_V,
    output reg         RDY
);
    reg [3:0] frame [0:16];
    reg [4:0] fidx, flen;
    wire [3:0] OP = frame[0];
    wire [2:0] A  = frame[1][2:0];
    wire [2:0] B  = frame[2][2:0];

    function mux16;
        input [15:0] v;
        input [3:0]  s;
        begin
            case (s)
                4'd0:  mux16 = v[0];   4'd1:  mux16 = v[1];
                4'd2:  mux16 = v[2];   4'd3:  mux16 = v[3];
                4'd4:  mux16 = v[4];   4'd5:  mux16 = v[5];
                4'd6:  mux16 = v[6];   4'd7:  mux16 = v[7];
                4'd8:  mux16 = v[8];   4'd9:  mux16 = v[9];
                4'd10: mux16 = v[10];  4'd11: mux16 = v[11];
                4'd12: mux16 = v[12];  4'd13: mux16 = v[13];
                4'd14: mux16 = v[14];  4'd15: mux16 = v[15];
            endcase
        end
    endfunction

    function apply_fn;
        input [1:0] fn;
        input s1, s2;
        begin
            case (fn)
                2'd0: apply_fn = s1 & s2;
                2'd1: apply_fn = s1 | s2;
                2'd2: apply_fn = s1 ^ s2;
                2'd3: apply_fn = ~(s1 & s2);
            endcase
        end
    endfunction

    wire k0,k1,k2,k3,k4,k5,k6,k7,k8,k9,k10;

    wire [15:0] s0 = {10'b0, B, A};
    wire [15:0] s1 = { 9'b0, k0, B, A};
    wire [15:0] s2 = { 8'b0, k1, k0, B, A};
    wire [15:0] s3 = { 7'b0, k2, k1, k0, B, A};
    wire [15:0] s4 = { 6'b0, k3, k2, k1, k0, B, A};
    wire [15:0] s5 = { 5'b0, k4, k3, k2, k1, k0, B, A};
    wire [15:0] s6 = { 4'b0, k5, k4, k3, k2, k1, k0, B, A};
    wire [15:0] s7 = { 3'b0, k6, k5, k4, k3, k2, k1, k0, B, A};
    wire [15:0] s8 = { 2'b0, k7, k6, k5, k4, k3, k2, k1, k0, B, A};
    wire [15:0] s9 = { 1'b0, k8, k7, k6, k5, k4, k3, k2, k1, k0, B, A};
    wire [15:0] s10= {        k9, k8, k7, k6, k5, k4, k3, k2, k1, k0, B, A};

    assign k0  = apply_fn(GENOME[1:0],   mux16(s0,  GENOME[5:2]),   mux16(s0,  GENOME[9:6]));
    assign k1  = apply_fn(GENOME[11:10], mux16(s1,  GENOME[15:12]), mux16(s1,  GENOME[19:16]));
    assign k2  = apply_fn(GENOME[21:20], mux16(s2,  GENOME[25:22]), mux16(s2,  GENOME[29:26]));
    assign k3  = apply_fn(GENOME[31:30], mux16(s3,  GENOME[35:32]), mux16(s3,  GENOME[39:36]));
    assign k4  = apply_fn(GENOME[41:40], mux16(s4,  GENOME[45:42]), mux16(s4,  GENOME[49:46]));
    assign k5  = apply_fn(GENOME[51:50], mux16(s5,  GENOME[55:52]), mux16(s5,  GENOME[59:56]));
    assign k6  = apply_fn(GENOME[61:60], mux16(s6,  GENOME[65:62]), mux16(s6,  GENOME[69:66]));
    assign k7  = apply_fn(GENOME[71:70], mux16(s7,  GENOME[75:72]), mux16(s7,  GENOME[79:76]));
    assign k8  = apply_fn(GENOME[81:80], mux16(s8,  GENOME[85:82]), mux16(s8,  GENOME[89:86]));
    assign k9  = apply_fn(GENOME[91:90], mux16(s9,  GENOME[95:92]), mux16(s9,  GENOME[99:96]));
    assign k10 = apply_fn(GENOME[101:100],mux16(s10, GENOME[105:102]), mux16(s10, GENOME[109:106]));

    reg [3:0] ans [0:3];
    reg [2:0] out_len, out_idx;
    reg [1:0] st;
    localparam IDLE = 2'd0, EXEC = 2'd1, OUT = 2'd2;

    always @(posedge CLK) begin
        if (!RST_N) begin
            fidx <= 0; flen <= 0; st <= IDLE;
            DOUT <= 0; DOUT_V <= 0; RDY <= 1;
            out_idx <= 0; out_len <= 0;
        end else case (st)
            IDLE: begin
                DOUT_V <= 0;
                if (DIN_V) begin
                    frame[fidx] <= DIN;
                    if (DIN_LAST) begin
                        flen <= fidx + 1; fidx <= 0; RDY <= 0; st <= EXEC;
                    end else fidx <= fidx + 1;
                end
            end
            EXEC: begin
                case (OP)
                    4'd8: begin
                        ans[0] <= {3'b0, k10};
                        out_len <= 3'd1;
                    end
                    default: out_len <= 3'd0;
                endcase
                out_idx <= 0; st <= OUT;
            end
            OUT: begin
                if (out_idx < out_len) begin
                    DOUT <= ans[out_idx]; DOUT_V <= 1'b1; out_idx <= out_idx + 1;
                end else begin
                    DOUT_V <= 1'b0; RDY <= 1'b1; st <= IDLE;
                end
            end
        endcase
    end
endmodule
