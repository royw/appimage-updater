#!/usr/bin/env python3

import re
import sys


for line in sys.stdin:
  if not re.match("^src/\\S+\\s+\\d+\\s+\\d+\\s+\\d+%\\s*", line):
    print(line.strip())
