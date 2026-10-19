`timescale 1ns/1ps
// Blinder Seed: keine Aufgabenlogik, nur ein pseudozufaelliger Zustand (xorshift64),
// der aus GENOME geladen wird. Pins gemaess Spezifikation.
// Zweck: Referenz-DUT, das BEWUSST keinen Fitness-Gradienten erzeugt.
module blind_seed (
    input  wire        CLK,
    input  wire        RST_N,
    input  wire [3:0]  DIN,
    input  wire        DIN_V,
    input  wire        DIN_LAST,
    input  wire        FB_OK,
    input  wire        FB_ERR,
    input  wire [63:0] GENOME,
    output reg  [3:0]  DOUT,
    output reg         DOUT_V,
    output reg         RDY
);
    reg [63:0] s;
    wire [63:0] s1 = s  ^ (s  << 13);
    wire [63:0] s2 = s1 ^ (s1 >> 7);
    wire [63:0] s3 = s2 ^ (s2 << 17);

    reg [1:0] st;
    reg [5:0] cnt;
    reg [2:0] nout;

    always @(posedge CLK) begin
        if (!RST_N) begin
            s      <= (GENOME == 64'd0) ? 64'h9E3779B97F4A7C15 : GENOME;
            DOUT   <= 4'd0;
            DOUT_V <= 1'b0;
            RDY    <= 1'b1;
            st     <= 2'd0;
            cnt    <= 6'd0;
            nout   <= 3'd0;
        end else begin
            s      <= s3;
            DOUT_V <= 1'b0;
            case (st)
                2'd0: if (DIN_V && DIN_LAST) begin
                    RDY <= 1'b0;
                    cnt <= {2'b00, s[3:0]};
                    st  <= 2'd1;
                end
                2'd1: begin
                    if (cnt != 0) cnt <= cnt - 1'b1;
                    else if (s[10]) begin
                        nout <= {1'b0, s[13:12]} + 3'd1;
                        st   <= 2'd2;
                    end else begin
                        RDY <= 1'b1;
                        st  <= 2'd0;
                    end
                end
                2'd2: begin
                    DOUT_V <= 1'b1;
                    DOUT   <= s[19:16];
                    nout   <= nout - 1'b1;
                    if (nout == 3'd1) begin
                        RDY <= 1'b1;
                        st  <= 2'd0;
                    end
                end
                default: st <= 2'd0;
            endcase
        end
    end
endmodule
