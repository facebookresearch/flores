# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#
#!/bin/bash

if [ $# -ne 2 ]; then
    echo "usage: $0 LANGUAGE INFILE"
    exit 1
fi
LANG=$1
INFILE=$2

ROOT=$(dirname "$0")

INDICNLP=$ROOT/indic_nlp_library
if [ ! -e $INDICNLP ]; then
    exit 1
fi

python2 $ROOT/indic_norm_tok.py --indic-nlp-path $INDICNLP --language $LANG $INFILE
