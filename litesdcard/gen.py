#!/usr/bin/env python3

#
# This file is part of LiteSDCard.
#
# Copyright (c) 2021 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""
LiteSDCard standalone core generator

LiteSDCard aims to be directly used as a python package when the SoC is created using LiteX. However,
for some use cases it could be interesting to generate a standalone verilog file of the core:
- integration of the core in a SoC using a more traditional flow.
- need to version/package the core.
- avoid Migen/LiteX dependencies.
- etc...
"""

import argparse

from migen import *

from litex.build.generic_platform import *
from litex.build.xilinx.platform import XilinxPlatform
from litex.build.altera.platform import AlteraPlatform
from litex.build.lattice.platform import LatticePlatform

from litex.soc.interconnect import wishbone
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

# IOs ----------------------------------------------------------------------------------------------

_io = [
    # Clk / Rst.
    ("clk", 0, Pins(1)),
    ("rst", 1, Pins(1)),

    # SDCard Pads.
    ("sdcard", 0,
        Subsignal("data", Pins(4)), # Note: Requires Pullup (internal or external).
        Subsignal("cmd",  Pins(1)), # Note: Requires Pullup (internal or external).
        Subsignal("clk",  Pins(1)),
        Subsignal("cd",   Pins(1)),
    ),
]

# LiteSDCard Core ----------------------------------------------------------------------------------

class LiteSDCardCore(SoCMini):
    def __init__(self, platform, clk_freq=int(100e6)):
        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = CRG(platform.request("clk"), platform.request("rst"))

        # SoCMini ----------------------------------------------------------------------------------
        SoCMini.__init__(self, platform, clk_freq=clk_freq)

        # Wishbone Control -------------------------------------------------------------------------
        wb_ctrl = wishbone.Interface()
        self.add_wb_master(wb_ctrl)
        platform.add_extension(wb_ctrl.get_ios("wb_ctrl"))
        self.comb += wb_ctrl.connect_to_pads(self.platform.request("wb_ctrl"), mode="slave")

        # Wishbone DMA -----------------------------------------------------------------------------
        wb_dma = self.cpu.dma_bus = wishbone.Interface()
        platform.add_extension(wb_dma.get_ios("wb_dma"))
        self.comb += wb_dma.connect_to_pads(self.platform.request("wb_dma"), mode="master")

        # SDCard -----------------------------------------------------------------------------------
        self.add_sdcard(name="sdcard")

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteSDCard standalone core generator.")
    parser.add_argument("--clk-freq", default="100e6",  help="Input Clk Frequency.")
    parser.add_argument("--vendor",   default="xilinx", help="FPGA Vendor.")
    args = parser.parse_args()

    # Convert/Check Arguments ----------------------------------------------------------------------------
    clk_freq     = int(float(args.clk_freq))
    platform_cls = {
        "xilinx"  : XilinxPlatform,
        "altera"  : AlteraPlatform,
        "intel"   : AlteraPlatform,
        "lattice" : LatticePlatform
    }[args.vendor]

    # Generate core --------------------------------------------------------------------------------
    platform = platform_cls(device="", io=_io)
    core     = LiteSDCardCore(platform, clk_freq=clk_freq)
    builder  = Builder(core, output_dir="build")
    builder.build(build_name="litesdcard_core", run=False)

if __name__ == "__main__":
    main()
