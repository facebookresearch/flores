# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#
#!/bin/bash

ROOT=$(dirname "$0")

INDICNLP=$ROOT/indic_nlp_library
if [ ! -e $INDICNLP ]; then
    echo "Cloning Indic NLP Library..."
    git -C $ROOT clone https://github.com/anoopkunchukuttan/indic_nlp_library.git
    pushd $INDICNLP
    git reset --hard 0a5e01f2701e0df5bc1f9905334cd7916d874c16
    popd
else
    echo "Indic is already pulled from github. Skipping."
fi
