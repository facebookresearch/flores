#!/usr/bin/env bash

if [[ -z "$fairseq" || -z "$flores101_dataset" ]]; then
  echo 'Need to specify the env vars fairseq and flores101_dataset.'
  exit 1
fi

source OCR_impact_BT/lang_codes.source

SRC_LANG_CODE=eng
SRC_MM100_LANG_CODE=en

for data_type in books_10k books_20k books_30k; do
  for trg_lang_code in "${!LANG_CODES[@]}"; do
    root_output='Data/backtranslation/data_books/'${data_type}
    root_checkpoint_out=${root_output}/model_checkpoints
    tensorboard_log_dir=${root_output}/logdir

    mkdir -p $root_output/SPM/train/
    mkdir -p $root_output/SPM/test/
    mkdir -p $root_output/SPM/val/

    trg_mm100_lang_code="${LANG_CODES[${trg_lang_code}]}"
    echo "${trg_lang_code}" "${trg_mm100_lang_code}"
    if [ ! -s "$root_output/generation_${trg_mm100_lang_code}_${SRC_MM100_LANG_CODE}/${SRC_LANG_CODE}.txt" ]; then
      echo "$root_output/generation_${trg_mm100_lang_code}_${SRC_MM100_LANG_CODE}/${SRC_LANG_CODE}.txt" doesn\'t exist
      continue
    fi
    checkpoint_out=${root_checkpoint_out}_${SRC_MM100_LANG_CODE}_${trg_mm100_lang_code}
    if [ -f "$checkpoint_out/checkpoint6.pt" ]; then
      echo "$checkpoint_out/checkpoint6.pt exists"
    else
      echo "$checkpoint_out/checkpoint6.pt doesn't exist!"

      python "$fairseq/scripts/spm_encode.py" \
        --model "$fairseq/flores101_mm100_615M/sentencepiece.bpe.model" \
        --output_format=piece \
        --inputs="$root_output/generation_${trg_mm100_lang_code}_${SRC_MM100_LANG_CODE}/${SRC_LANG_CODE}.txt" \
        --outputs="$root_output/SPM/train/spm.${SRC_MM100_LANG_CODE}-${trg_mm100_lang_code}.${SRC_MM100_LANG_CODE}"

      python "$fairseq/scripts/spm_encode.py" \
        --model "$fairseq/flores101_mm100_615M/sentencepiece.bpe.model" \
        --output_format=piece \
        --inputs="$root_output/${trg_lang_code}_mono.txt" \
        --outputs="$root_output/SPM/train/spm.${SRC_MM100_LANG_CODE}-${trg_mm100_lang_code}.${trg_mm100_lang_code}"

      python "$fairseq/scripts/spm_encode.py" \
        --model "$fairseq/flores101_mm100_615M/sentencepiece.bpe.model" \
        --output_format=piece \
        --inputs="$flores101_dataset/dev/${SRC_LANG_CODE}.dev" \
        --outputs="$root_output/SPM/val/spm.${SRC_MM100_LANG_CODE}-${trg_mm100_lang_code}.${SRC_MM100_LANG_CODE}"

      python "$fairseq/scripts/spm_encode.py" \
        --model "$fairseq/flores101_mm100_615M/sentencepiece.bpe.model" \
        --output_format=piece \
        --inputs="$flores101_dataset/dev/${trg_lang_code}.dev" \
        --outputs="$root_output/SPM/val/spm.${SRC_MM100_LANG_CODE}-${trg_mm100_lang_code}.${trg_mm100_lang_code}"

      python "$fairseq/scripts/spm_encode.py" \
        --model "$fairseq/flores101_mm100_615M/sentencepiece.bpe.model" \
        --output_format=piece \
        --inputs="$flores101_dataset/devtest/${SRC_LANG_CODE}.devtest" \
        --outputs="$root_output/SPM/test/spm.${SRC_MM100_LANG_CODE}-${trg_mm100_lang_code}.${SRC_MM100_LANG_CODE}"

      python "$fairseq/scripts/spm_encode.py" \
        --model "$fairseq/flores101_mm100_615M/sentencepiece.bpe.model" \
        --output_format=piece \
        --inputs="$flores101_dataset/devtest/${trg_lang_code}.devtest" \
        --outputs="$root_output/SPM/test/spm.${SRC_MM100_LANG_CODE}-${trg_mm100_lang_code}.${trg_mm100_lang_code}"

      # #### Binarization
      fairseq-preprocess \
        --source-lang ${SRC_MM100_LANG_CODE} --target-lang "${trg_mm100_lang_code}" \
        --validpref "$root_output/SPM/val/spm.${SRC_MM100_LANG_CODE}-${trg_mm100_lang_code}" \
        --trainpref "$root_output/SPM/train/spm.${SRC_MM100_LANG_CODE}-${trg_mm100_lang_code}" \
        --testpref "$root_output/SPM/test/spm.${SRC_MM100_LANG_CODE}-${trg_mm100_lang_code}" \
        --thresholdsrc 0 --thresholdtgt 0 \
        --destdir "$root_output/data_bin_${SRC_MM100_LANG_CODE}_${trg_mm100_lang_code}" \
        --srcdict "$fairseq/flores101_mm100_615M/dict.txt" --tgtdict "$fairseq/flores101_mm100_615M/dict.txt"

      lang_pairs="${SRC_MM100_LANG_CODE}-${trg_mm100_lang_code}"
      fairseq-train --fp16 \
        --memory-efficient-fp16 \
        "$root_output/data_bin_${SRC_MM100_LANG_CODE}_${trg_mm100_lang_code}" \
        --finetune-from-model "${CHECKPOINT_IN}" \
        --task 'translation_multi_simple_epoch' \
        --arch transformer_wmt_en_de_big --share-all-embeddings \
        --encoder-layers 12 --decoder-layers 12 \
        --encoder-attention-heads 16 --decoder-attention-heads 16 \
        --encoder-embed-dim 1024 --decoder-embed-dim 1024 \
        --encoder-ffn-embed-dim 4096 --decoder-ffn-embed-dim 4096 \
        --encoder-normalize-before --decoder-normalize-before \
        --dropout 0.1 --attention-dropout 0.1 --relu-dropout 0.0 \
        --weight-decay 0.0 \
        --label-smoothing 0.1 --criterion label_smoothed_cross_entropy \
        --optimizer adam --adam-betas '(0.9, 0.98)' --clip-norm 0 --adam-eps 1e-08 \
        --lr-scheduler inverse_sqrt --lr 0.0002 --warmup-updates 4000 --warmup-init-lr 1e-7 --max-update 10000000 \
        --max-tokens 3400 \
        --encoder-langtok 'src' \
        --decoder-langtok \
        --lang-pairs "$lang_pairs" \
        --sampling-method 'temperature' --sampling-temperature 5.0 \
        --source-lang ${SRC_MM100_LANG_CODE} --target-lang "${trg_mm100_lang_code}" \
        --update-freq 2 \
        --seed 2 \
        --max-source-positions 1024 --max-target-positions 1024 \
        --max-epoch 6 --save-interval 3 \
        --tensorboard-logdir ${tensorboard_log_dir} \
        --save-dir "${checkpoint_out}"

      python -c "import torch; torch.cuda.empty_cache()"
    fi

    if [ -s "$root_output/generation_${SRC_MM100_LANG_CODE}_${trg_mm100_lang_code}/${trg_lang_code}.txt" ]; then
      echo "$root_output/generation_${SRC_MM100_LANG_CODE}_${trg_mm100_lang_code}/${trg_lang_code}.txt" exists
    else
      echo "$root_output/generation_${SRC_MM100_LANG_CODE}_${trg_mm100_lang_code}/${trg_lang_code}.txt" doesn\'t exist

      fairseq-generate \
        "$root_output/data_bin_${SRC_MM100_LANG_CODE}_${trg_mm100_lang_code}" \
        --batch-size 512 \
        --path "${checkpoint_out}/checkpoint_best.pt" \
        --fixed-dictionary "$fairseq/flores101_mm100_615M/dict.txt" \
        -s ${SRC_MM100_LANG_CODE} -t "${trg_mm100_lang_code}" \
        --remove-bpe 'sentencepiece' \
        --beam 5 \
        --task translation_multi_simple_epoch \
        --lang-pairs "$fairseq/flores101_mm100_615M/language_pairs.txt" \
        --decoder-langtok --encoder-langtok src \
        --gen-subset test \
        --fp16 \
        --dataset-impl mmap \
        --distributed-world-size 1 --distributed-no-spawn \
        --results-path "$root_output/generation_${SRC_MM100_LANG_CODE}_${trg_mm100_lang_code} "
    fi

    if [ -s "$root_output/generation_${SRC_MM100_LANG_CODE}_${trg_mm100_lang_code}/generate-test.txt" ]; then
      echo "Evaluation: " $root_output/results.txt
      ## clean fairseq generated file to only create hypotheses file.
      grep -P '^H-' "$root_output/generation_${SRC_MM100_LANG_CODE}_${trg_mm100_lang_code}/generate-test.txt" |
        cut -c 3- |
        sort -n -k 1 |
        awk -F "\t" '{print $NF}' \
          >"$root_output/generation_${SRC_MM100_LANG_CODE}_${trg_mm100_lang_code}/${trg_lang_code}.txt"
      ## Evaluate
      echo "${data_type} ${trg_lang_code}" >>$root_output/results.txt
      sacrebleu \
        "$flores101_dataset/devtest/${trg_lang_code}.devtest" \
        --tokenize spm \
        <"$root_output/generation_${SRC_MM100_LANG_CODE}_${trg_mm100_lang_code}/${trg_lang_code}.txt" \
        >>$root_output/results.txt
    fi
  done
done
