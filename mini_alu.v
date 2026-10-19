`timescale 1ns/1ps
// mini_alu: konfigurierbares DUT fuer den GA.
// GENOME[7:0] steuert echte Muxe. Jedes Bit ist eine Fitness-Stufe.
//   0-3: ALU-Opcode-Mapping (calc)
//   4:   RAM enable          (mem)
//   5:   cmp-Richtung        (cmp)
//   6:   Transitivitaet      (cmp_hard)
//   7:   Cipher-Key-XOR      (cipher)
module mini_alu (
    input  wire        CLK, RST_N,
    input  wire [3:0]  DIN,
    input  wire        DIN_V, DIN_LAST,
    input  wire        FB_OK, FB_ERR,
    input  wire [63:0] GENOME,
    output reg  [3:0]  DOUT,
    output reg         DOUT_V,
    output reg         RDY
);
    reg [3:0] frame [0:16];
    reg [4:0] fidx, flen;

    wire [3:0] OP = frame[0];
    wire [3:0] A  = frame[1];
    wire [3:0] B  = frame[2];
    wire [3:0] O  = frame[3];

    // ---- CALC: vier 2:1-Muxe, gesteuert von GENOME[3:0] ----
    wire [7:0] s_add = {4'd0, A} + {4'd0, B};
    wire [7:0] s_sub = {4'd0, A} - {4'd0, B};
    wire [7:0] s_and = {4'd0, A & B};
    wire [7:0] s_xor = {4'd0, A ^ B};
    reg  [7:0] alu;
    always @(*) begin
        case (O)
            4'd0: alu = GENOME[0] ? s_add : s_sub;
            4'd1: alu = GENOME[1] ? s_sub : s_add;
            4'd2: alu = GENOME[2] ? s_and : s_xor;
            4'd3: alu = GENOME[3] ? s_xor : s_and;
            default: alu = 8'd0;
        endcase
    end

    // ---- Speicher ----
    reg [3:0]  vals [0:15];
    reg [15:0] rel  [0:15];
    reg [1:0]  cmp_mode;
    reg [3:0]  cbuf [0:15];

    // ---- Antwort-Puffer ----
    reg [3:0] ans [0:15];
    reg [4:0] out_len, out_idx;

    // ---- Relationshuelle (kombinatorisch) ----
    wire [15:0] row_a = rel[A];
    wire [15:0] row_b = rel[B];
    wire rel_direct_ab = row_a[B];
    wire rel_direct_ba = row_b[A];

    reg [15:0] col_a, col_b, tmp_row;
    integer zz;
    always @(*) begin
        col_a = 16'd0; col_b = 16'd0;
        for (zz = 0; zz < 16; zz = zz + 1) begin
            tmp_row = rel[zz];
            col_a[zz] = tmp_row[A];
            col_b[zz] = tmp_row[B];
        end
    end
    wire rel_trans_ab = |(row_a & col_b);
    wire rel_trans_ba = |(row_b & col_a);

    // ---- FSM ----
    localparam IDLE = 2'd0, EXEC = 2'd1, OUT = 2'd2;
    reg [1:0] st;
    integer i, j;

    always @(posedge CLK) begin
        if (!RST_N) begin
            fidx <= 0; flen <= 0; st <= IDLE;
            DOUT <= 0; DOUT_V <= 0; RDY <= 1;
            out_idx <= 0; out_len <= 0; cmp_mode <= 0;
            for (i = 0; i < 16; i = i + 1) begin
                vals[i] <= 0; rel[i] <= 16'd0; cbuf[i] <= 0;
            end
        end else case (st)
            IDLE: begin
                DOUT_V <= 0;
                if (DIN_V) begin
                    frame[fidx] <= DIN;
                    if (DIN_LAST) begin
                        flen <= fidx + 1;
                        fidx <= 0;
                        RDY  <= 0;
                        st   <= EXEC;
                    end else fidx <= fidx + 1;
                end
            end

            EXEC: begin
                case (OP)
                    4'd1: begin
                        ans[0] <= alu[7:4];
                        ans[1] <= alu[3:0];
                        out_len <= 5'd2;
                    end
                    4'd2: begin
                        vals[A]  <= B;
                        cmp_mode <= 2'd1;
                        out_len  <= 5'd0;
                    end
                    4'd3: begin
                        ans[0]  <= vals[A];
                        out_len <= 5'd1;
                    end
                    4'd4: begin
                        rel[A][B] <= 1'b1;
                        cmp_mode  <= 2'd2;
                        out_len   <= 5'd0;
                    end
                    4'd5: begin
                        if (cmp_mode == 2'd1) begin
                            if (vals[A] > vals[B])
                                ans[0] <= GENOME[5] ? 4'd1 : 4'd2;
                            else
                                ans[0] <= GENOME[5] ? 4'd2 : 4'd1;
                        end else begin
                            if (GENOME[6]) begin
                                if (rel_direct_ab | rel_trans_ab)
                                    ans[0] <= GENOME[5] ? 4'd1 : 4'd2;
                                else if (rel_direct_ba | rel_trans_ba)
                                    ans[0] <= GENOME[5] ? 4'd2 : 4'd1;
                                else
                                    ans[0] <= 4'd0;
                            end else begin
                                if (rel_direct_ab)
                                    ans[0] <= GENOME[5] ? 4'd1 : 4'd2;
                                else if (rel_direct_ba)
                                    ans[0] <= GENOME[5] ? 4'd2 : 4'd1;
                                else
                                    ans[0] <= 4'd0;
                            end
                        end
                        out_len <= 5'd1;
                    end
                    4'd6: begin
                        for (i = 0; i < 16; i = i + 1)
                            cbuf[i] <= frame[i + 1];
                        out_len <= 5'd0;
                    end
                    4'd7: begin
                        for (j = 0; j < 16; j = j + 1) begin
                            if (j < A) begin
                                if (GENOME[7])
                                    ans[j] <= cbuf[j] ^ j[3:0];
                                else
                                    ans[j] <= cbuf[j];
                            end
                        end
                        out_len <= {1'b0, A};
                    end
                    default: out_len <= 5'd0;
                endcase
                out_idx <= 0;
                st <= OUT;
            end

            OUT: begin
                if (out_idx < out_len) begin
                    DOUT    <= ans[out_idx];
                    DOUT_V  <= 1'b1;
                    out_idx <= out_idx + 1;
                end else begin
                    DOUT_V <= 1'b0;
                    RDY    <= 1'b1;
                    st     <= IDLE;
                end
            end
        endcase
    end
endmodule
