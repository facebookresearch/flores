# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#
#!/bin/bash

SRC="ps"
SRCS="ps km hi fa"
TGT=en

BPESIZE=15000
TRAIN_MINLEN=1  # remove sentences with <1 BPE token
TRAIN_MAXLEN=250  # remove sentences with >250 BPE tokens 

ROOT=$(dirname "$0")
SCRIPTS=$ROOT/scripts
DATA=$ROOT/data
mkdir -p $DATA 

SPM_TRAIN=$SCRIPTS/spm_train.py
SPM_ENCODE=$SCRIPTS/spm_encode.py

TRAIN_SETS_PS=(
  "all-clean-ps/GNOME.en-ps"
  "all-clean-ps/KDE4.en-ps"
  "all-clean-ps/Tatoeba.en-ps"
  "all-clean-ps/Ubuntu.en-ps"
  "all-clean-ps/wikimedia.en-ps"
)
TRAIN_SETS_KM=(
  "all-clean-km/GlobalVoices.en-km"
  "all-clean-km/GNOME.en-km"
  "all-clean-km/KDE4.en-km"
  "all-clean-km/Tatoeba.en-km"
  "all-clean-km/Ubuntu.en-km"
)
TRAIN_SETS_HI=("all-clean-hi/IITB.en-hi")
DATA_SETS_FA=(
  "all-clean-fa/GlobalVoices.en-fa"
  "all-clean-fa/GNOME.en-fa"
  "all-clean-fa/infopankki.en-fa"
  "all-clean-fa/KDE4.en-fa"
  "all-clean-fa/OpenSubtitles.en-fa"
  "all-clean-fa/QED.en-fa"
  "all-clean-fa/Tanzil.en-fa"
  "all-clean-fa/TED2013.en-fa"
  "all-clean-fa/TEP.en-fa"
  "all-clean-fa/Ubuntu.en-fa"
  "all-clean-fa/Wikipedia.en-fa"
)

echo "Aggregating splits"
for FILE in "${TRAIN_SETS_PS[@]}" ; do cat "${DATA}/$FILE.ps"; done > $DATA/undeduped-train.ps-en.ps
for FILE in "${TRAIN_SETS_PS[@]}" ; do cat "${DATA}/$FILE.en"; done > $DATA/undeduped-train.ps-en.en
for FILE in "${TRAIN_SETS_KM[@]}" ; do cat "${DATA}/$FILE.km"; done > $DATA/undeduped-train.km-en.km
for FILE in "${TRAIN_SETS_KM[@]}" ; do cat "${DATA}/$FILE.en"; done > $DATA/undeduped-train.km-en.en
for FILE in "${TRAIN_SETS_HI[@]}" ; do cat "${DATA}/$FILE.hi"; done > $DATA/undeduped-train.hi-en.hi
for FILE in "${TRAIN_SETS_HI[@]}" ; do cat "${DATA}/$FILE.en"; done > $DATA/undeduped-train.hi-en.en
for FILE in "${DATA_SETS_FA[@]}"  ; do cat "${DATA}/$FILE.fa"; done | awk 'NR % 1500 >  1' > $DATA/undeduped-train.fa-en.fa
for FILE in "${DATA_SETS_FA[@]}"  ; do cat "${DATA}/$FILE.en"; done | awk 'NR % 1500 >  1' > $DATA/undeduped-train.fa-en.en
for FILE in "${DATA_SETS_FA[@]}"  ; do cat "${DATA}/$FILE.fa"; done | awk 'NR % 1500 == 0' > $DATA/undeduped-valid.fa-en.fa
for FILE in "${DATA_SETS_FA[@]}"  ; do cat "${DATA}/$FILE.en"; done | awk 'NR % 1500 == 0' > $DATA/undeduped-valid.fa-en.en
for FILE in "${DATA_SETS_FA[@]}"  ; do cat "${DATA}/$FILE.fa"; done | awk 'NR % 1500 == 1' > $DATA/undeduped-test.fa-en.fa
for FILE in "${DATA_SETS_FA[@]}"  ; do cat "${DATA}/$FILE.en"; done | awk 'NR % 1500 == 1' > $DATA/undeduped-test.fa-en.en
echo "Deduplicating splits"
dedupe () {
  dedupe_set=$1
  dedupe_lang=$2
  python3 scripts/deduplicate.py \
  --input-src  $DATA/undeduped-$dedupe_set.$dedupe_lang-en.$dedupe_lang \
  --input-tgt  $DATA/undeduped-$dedupe_set.$dedupe_lang-en.en \
  --output-src $DATA/$dedupe_set.$dedupe_lang-en.$dedupe_lang \
  --output-tgt $DATA/$dedupe_set.$dedupe_lang-en.en
}
dedupe "train" "ps"
dedupe "train" "km"
dedupe "train" "hi"
dedupe "train" "fa"
dedupe "valid" "fa"
dedupe "test"  "fa"
cat "${DEVTEST_PSKM}/ps-en.dev.ps"     > $DATA/valid.ps-en.ps
cat "${DEVTEST_PSKM}/ps-en.dev.en"     > $DATA/valid.ps-en.en
cat "${DEVTEST_PSKM}/ps-en.devtest.ps" > $DATA/test.ps-en.ps
cat "${DEVTEST_PSKM}/ps-en.devtest.en" > $DATA/test.ps-en.en
cat "${DEVTEST_PSKM}/km-en.dev.km"     > $DATA/valid.km-en.km
cat "${DEVTEST_PSKM}/km-en.dev.en"     > $DATA/valid.km-en.en
cat "${DEVTEST_PSKM}/km-en.devtest.km" > $DATA/test.km-en.km
cat "${DEVTEST_PSKM}/km-en.devtest.en" > $DATA/test.km-en.en
cat "${DEVTEST_HI}/dev.hi"          > $DATA/valid.hi-en.hi
cat "${DEVTEST_HI}/dev.en"          > $DATA/valid.hi-en.en
cat "${DEVTEST_HI}/test.hi"         > $DATA/test.hi-en.hi
cat "${DEVTEST_HI}/test.en"         > $DATA/test.hi-en.en
echo "Creating abridged train sets for BPE, so all languages are similarly well-represented"
cat $DATA/train.ps-en.ps | head -100000 >  $DATA/abridged.ps
cat $DATA/train.km-en.km | head -100000 >  $DATA/abridged.km
cat $DATA/train.hi-en.hi | head -100000 >  $DATA/abridged.hi
cat $DATA/train.fa-en.fa | head -100000 >  $DATA/abridged.fa
cat $DATA/train.ps-en.en | head -100000 >  $DATA/abridged.en
cat $DATA/train.km-en.en | head -100000 >> $DATA/abridged.en
cat $DATA/train.hi-en.en | head -100000 >> $DATA/abridged.en
cat $DATA/train.fa-en.en | head -100000 >> $DATA/abridged.en
echo "Concatenating target data"
cat $DATA/train.ps-en.en >  $DATA/train-concatenated.en
cat $DATA/train.km-en.en >> $DATA/train-concatenated.en
cat $DATA/train.hi-en.en >> $DATA/train-concatenated.en
cat $DATA/train.fa-en.en >> $DATA/train-concatenated.en
cat $DATA/valid.ps-en.en >  $DATA/valid-concatenated.en
cat $DATA/valid.km-en.en >> $DATA/valid-concatenated.en
cat $DATA/valid.hi-en.en >> $DATA/valid-concatenated.en
cat $DATA/valid.fa-en.en >> $DATA/valid-concatenated.en
cat $DATA/test.ps-en.en  >  $DATA/test-concatenated.en
cat $DATA/test.km-en.en  >> $DATA/test-concatenated.en
cat $DATA/test.hi-en.en  >> $DATA/test-concatenated.en
cat $DATA/test.fa-en.en  >> $DATA/test-concatenated.en
echo "Learning BPE with sentencepiece"
python $SPM_TRAIN \
  --input=$DATA/abridged.ps,$DATA/abridged.km,$DATA/abridged.hi,$DATA/abridged.fa,$DATA/abridged.en \
  --model_prefix=$DATA/sentencepiece.bpe \
  --vocab_size=$BPESIZE \
  --character_coverage=1.0 \
  --model_type=bpe
echo "Encoding"
for SOMESRC in $SRCS; do
  python $SPM_ENCODE \
    --model $DATA/sentencepiece.bpe.model \
    --output_format=piece \
    --inputs $DATA/train.$SOMESRC-en.$SOMESRC $DATA/train.$SOMESRC-en.en \
    --outputs $DATA/train.bpe.$SOMESRC-en.$SOMESRC $DATA/train.bpe.$SOMESRC-en.en \
    --min-len $TRAIN_MINLEN --max-len $TRAIN_MAXLEN
  for SPLIT in "valid" "test"; do
    python $SPM_ENCODE \
      --model $DATA/sentencepiece.bpe.model \
      --output_format=piece \
      --inputs $DATA/$SPLIT.$SOMESRC-en.$SOMESRC $DATA/$SPLIT.$SOMESRC-en.en \
      --outputs $DATA/$SPLIT.bpe.$SOMESRC-en.$SOMESRC $DATA/$SPLIT.bpe.$SOMESRC-en.en
  done
done
echo "Converting sentencepiece vocabulary into fairseq dictionary"
tail -n +4 $DATA/sentencepiece.bpe.vocab | awk -F'\t' 'BEGIN{OFS=" "} {print $1, 100}' > $DATA/vocab
echo "Preprocessing"
for SOMESRC in $SRCS; do
  echo "Binarizing ${SOMESRC}"
  fairseq-preprocess \
    --source-lang $SOMESRC --target-lang en \
    --destdir $DATA \
    --joined-dictionary \
    --workers 4 \
    --trainpref $DATA/train.bpe.$SOMESRC-en \
    --validpref $DATA/valid.bpe.$SOMESRC-en \
    --testpref  $DATA/test.bpe.$SOMESRC-en \
    --srcdict $DATA/vocab
  mv "${DATA}/dict.en.txt" "${DATA}/dict.en.txt-moved"
done
mv "${DATA}/dict.en.txt-moved" "${DATA}/dict.en.txt"
