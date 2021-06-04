# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#
#!/bin/bash
# Downloads the data and creates data/all-clean.tgz within the current directory

set -e
set -o pipefail
set -x

ROOT=$(dirname "$0")
DATA=$ROOT/data/mono
NUM_MONO=5000000

REMOVE_FILE_PATHS=()

# Download data
download_data() {
  CORPORA=$1
  URL=$2

  echo "Downloading $URL"
  wget -c $URL -O $CORPORA --no-check-certificate || rm -f $CORPORA
  if [ -f $CORPORA ]; then
    echo "$URL successfully downloaded."
  else
    echo "$URL not successfully downloaded."
    exit -1
  fi
}

# Prepare parallel data to generate sentence piece model
if ! [[ -f data-bin/wiki_ne_en_bpe5000/sentencepiece.bpe.model ]]; then
  bash prepare-neen.sh
fi
if ! [[ -f data-bin/wiki_si_en_bpe5000/sentencepiece.bpe.model ]]; then
  bash prepare-sien.sh
fi

mkdir -p $DATA

if ! [[ -f $DATA/mono.sample"$NUM_MONO".en ]]; then
  download_data wikipedia_en_filtered.gz https://dl.fbaipublicfiles.com/fairseq/data/wikipedia.en_filtered.gz
  REMOVE_FILE_PATHS+=( wikipedia_en_filtered.gz )
  gunzip -c wikipedia_en_filtered.gz > $DATA/mono.en
  cat $DATA/mono.en | ./scripts/shuf.py --seed 42 -n $NUM_MONO > $DATA/mono.sample"$NUM_MONO".en
fi

if ! [[ -f $DATA/mono.sample"$NUM_MONO".ne ]]; then
  download_data wikipedia_ne_filtered.gz https://dl.fbaipublicfiles.com/fairseq/data/wikipedia.ne_filtered.gz
  download_data commoncrawl.deduped.ne.xz http://data.statmt.org/wmt19/parallel-corpus-filtering/commoncrawl.deduped.ne.xz
  REMOVE_FILE_PATHS+=( wikipedia_ne_filtered.gz commoncrawl.deduped.ne.xz )
  gunzip -c wikipedia_ne_filtered.gz > $DATA/mono.ne
  unxz -c commoncrawl.deduped.ne.xz >> $DATA/mono.ne
  cat $DATA/mono.ne | ./scripts/shuf.py --seed 43 -n $NUM_MONO > $DATA/mono.sample"$NUM_MONO".ne
fi

if ! [[ -f $DATA/mono.sample"$NUM_MONO".si ]]; then
  download_data wikipedia_si_filtered.gz https://dl.fbaipublicfiles.com/fairseq/data/wikipedia.si_filtered.gz
  download_data commoncrawl.deduped.si.xz http://data.statmt.org/wmt19/parallel-corpus-filtering/commoncrawl.deduped.si.xz
  REMOVE_FILE_PATHS+=( wikipedia_si_filtered.gz commoncrawl.deduped.si.xz )
  gunzip -c wikipedia_si_filtered.gz > $DATA/mono.si
  unxz -c commoncrawl.deduped.si.xz >> $DATA/mono.si
  cat $DATA/mono.si | ./scripts/shuf.py --seed 44 -n $NUM_MONO > $DATA/mono.sample"$NUM_MONO".si
fi

ROOT=$(dirname "$0")
SCRIPTS=$ROOT/scripts
SRC_TOKENIZER="bash $SCRIPTS/indic_norm_tok.sh"
TGT_TOKENIZER="cat"  # learn target-side BPE over untokenized (raw) text
SPM_TRAIN=$SCRIPTS/spm_train.py
SPM_ENCODE=$SCRIPTS/spm_encode.py

echo "pre-processing monolingual data..."
mkdir -p $DATA/neen
bash $SCRIPTS/download_indic.sh
if ! [[ -f $DATA/neen/mono.bpe.ne ]]; then
  $SRC_TOKENIZER ne $DATA/mono.sample"$NUM_MONO".ne | python $SPM_ENCODE \
    --model data-bin/wiki_ne_en_bpe5000/sentencepiece.bpe.model \
    --output_format=piece \
    --inputs - \
    --outputs $DATA/neen/mono.bpe.ne
fi

if ! [[ -f $DATA/neen/mono.bpe.en ]]; then
  $TGT_TOKENIZER $DATA/mono.sample"$NUM_MONO".en | python $SPM_ENCODE \
    --model data-bin/wiki_ne_en_bpe5000/sentencepiece.bpe.model \
    --output_format=piece \
    --inputs - \
    --outputs $DATA/neen/mono.bpe.en
fi


if ! [[ -f $DATA/sien/mono.bpe.si ]]; then
  mkdir -p $DATA/sien
  $SRC_TOKENIZER si $DATA/mono.sample"$NUM_MONO".si | python $SPM_ENCODE \
    --model data-bin/wiki_si_en_bpe5000/sentencepiece.bpe.model \
    --output_format=piece \
    --inputs - \
    --outputs $DATA/sien/mono.bpe.si
fi

if ! [[ -f $DATA/sien/mono.bpe.en ]]; then
  $TGT_TOKENIZER $DATA/mono.sample"$NUM_MONO".en | python $SPM_ENCODE \
    --model data-bin/wiki_si_en_bpe5000/sentencepiece.bpe.model \
    --output_format=piece \
    --inputs - \
    --outputs $DATA/sien/mono.bpe.en
fi

# Remove the temporary files
for ((i=0;i<${#REMOVE_FILE_PATHS[@]};++i)); do
  rm -rf ${REMOVE_FILE_PATHS[i]}
done
