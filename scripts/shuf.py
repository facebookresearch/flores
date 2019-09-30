#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#


import argparse
import numpy as np
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num-lines', '-n', default=None, help='Output the first n lines after shuffling', type=int)
    parser.add_argument('--seed', '-s', default=42, help='Random seed', type=int)
    args = parser.parse_args()

    lines = [line for line in sys.stdin]
    args.num_lines = min(args.num_lines or len(lines), len(lines))

    np.random.seed(args.seed)
    for i in np.random.choice(len(lines), args.num_lines, replace=False):
        print(lines[i], end='')


if __name__ == "__main__":
    main()
