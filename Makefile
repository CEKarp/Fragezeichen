SIM ?= icarus
TOPLEVEL_LANG = verilog

DUT ?= mini_alu
VERILOG_SOURCES = $(shell pwd)/$(DUT).v

TOPLEVEL = $(DUT)
MODULE   = host
COCOTB_TOPLEVEL     = $(DUT)
COCOTB_TEST_MODULES = host

include $(shell cocotb-config --makefiles)/Makefile.sim
