# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#
#!/usr/bin/env python

import os
from subprocess import check_output
import subprocess


def check_last_line(filepath, s, is_exact=False):
    if not os.path.exists(filepath):
        return False

    last_line = check_output(f'tail -n 1 {filepath}', shell=True).decode('utf-8').strip()
    return (s == last_line) if is_exact else (s in last_line)


def count_line(filename):
    try:
        return int(check_output(f'wc -l {filename} | cut -d " " -f1', shell=True))
    except (subprocess.CalledProcessError, ValueError) as e:
        return 0
