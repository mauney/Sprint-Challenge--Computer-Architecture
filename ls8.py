#!/usr/bin/env python3

"""Main."""

import sys
from cpu import *

if len(sys.argv) != 2:
    print('Usage: ls8.py path/file_to_load')
    sys.exit(1)
program = sys.argv[1]
# program = 'ls8/examples/call.ls8'

cpu = CPU()

cpu.load(program)
cpu.run()
