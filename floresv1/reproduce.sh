# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#
#!/bin/bash
# Script to reproduce iterative back-translation baseline

SUPPORT_LANG_PAIRS="ne_en|en_ne|si_en|en_si"

if [[ $# -lt 1 ]] || ! [[ "$1" =~ ^($SUPPORT_LANG_PAIRS)$ ]]; then
  echo "Usage: $0 LANGUAGE_PAIR($SUPPORT_LANG_PAIRS)"
  exit 1
fi

LANG_PAIR=$1

if [[ $LANG_PAIR = "ne_en" ]]; then
  python scripts/train.py --config configs/neen.json --databin $PWD/data-bin/wiki_ne_en_bpe5000/
elif [[ $LANG_PAIR = "en_ne" ]]; then
  python scripts/train.py --config configs/enne.json --databin $PWD/data-bin/wiki_ne_en_bpe5000/
elif [[ $LANG_PAIR = "si_en" ]]; then
  python scripts/train.py --config configs/sien.json --databin $PWD/data-bin/wiki_si_en_bpe5000/
elif [[ $LANG_PAIR = "en_si" ]]; then
  python scripts/train.py --config configs/ensi.json --databin $PWD/data-bin/wiki_si_en_bpe5000/
fi
