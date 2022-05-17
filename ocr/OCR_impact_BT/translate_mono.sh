#!/usr/bin/env bash

if [[ -z "$fairseq" ]]; then
  echo 'Need to specify the env var fairseq.'
  exit 1
fi

source OCR_impact_BT/lang_codes.source

TRG_LANG_CODE=eng
TRG_MM100_LANG_CODE=en

SIZE=20k

for src_lang_code in "${!LANG_CODES[@]}"; do
  for error_rate in {1..22..2}; do
    for error_type in replace insert delete; do
      data_type=${error_rate}/${error_type}
      root_output=Data/backtranslation/data_cer_$SIZE/${data_type}
      mkdir -p $root_output/SPM/mono/
      echo $root_output

      src_mm100_lang_code="${LANG_CODES[${src_lang_code}]}"
      if [ ! -f "$root_output/${src_lang_code}_mono.txt" ]; then
        echo "$root_output/${src_lang_code}_mono.txt" doesn\'t exist
        continue
      fi
      generation_file=$root_output/generation_${src_mm100_lang_code}_${TRG_MM100_LANG_CODE}/${TRG_LANG_CODE}.txt
      echo "${src_lang_code}" "${src_mm100_lang_code}"
      if [ -s "${generation_file}" ] && [ "$(wc -l < "$generation_file")" -eq 20000 ]; then
        echo "${generation_file} exists and has 20000 lines."
        continue
      else
        echo "$generation_file doesn't exist or hasn't 20000 lines"
      fi
      python "$fairseq/scripts/spm_encode.py" \
        --model "$fairseq/flores101_mm100_615M/sentencepiece.bpe.model" \
        --output_format=piece \
        --inputs="$root_output/${src_lang_code}_mono.txt" \
        --outputs="$root_output/SPM/mono/spm.${src_mm100_lang_code}-${TRG_MM100_LANG_CODE}.${src_mm100_lang_code}"

      python "$fairseq/scripts/spm_encode.py" \
        --model "$fairseq/flores101_mm100_615M/sentencepiece.bpe.model" \
        --output_format=piece \
        --inputs="$root_output/${src_lang_code}_mono.txt" \
        --outputs="$root_output/SPM/mono/spm.${src_mm100_lang_code}-${TRG_MM100_LANG_CODE}.${TRG_MM100_LANG_CODE}"

      fairseq-preprocess \
        --source-lang "${src_mm100_lang_code}" --target-lang ${TRG_MM100_LANG_CODE} \
        --trainpref "$root_output/SPM/mono/spm.${src_mm100_lang_code}-${TRG_MM100_LANG_CODE}" \
        --thresholdsrc 0 --thresholdtgt 0 \
        --destdir "$root_output/data_bin_${src_mm100_lang_code}_${TRG_MM100_LANG_CODE}" \
        --srcdict "$fairseq/flores101_mm100_615M/dict.txt" --tgtdict "$fairseq/flores101_mm100_615M/dict.txt"

      fairseq-generate \
        "$root_output/data_bin_${src_mm100_lang_code}_${TRG_MM100_LANG_CODE}" \
        --batch-size 64 \
        --skip-invalid-size-inputs-valid-test \
        --path "$fairseq/flores101_mm100_615M/model.pt" \
        --fixed-dictionary "$fairseq/flores101_mm100_615M/dict.txt" \
        -s "${src_mm100_lang_code}" -t ${TRG_MM100_LANG_CODE} \
        --remove-bpe 'sentencepiece' \
        --beam 5 \
        --fp16 \
        --task translation_multi_simple_epoch \
        --lang-pairs "$fairseq/flores101_mm100_615M/language_pairs.txt" \
        --decoder-langtok --encoder-langtok src \
        --gen-subset train \
        --dataset-impl mmap \
        --distributed-world-size 1 --distributed-no-spawn \
        --results-path "$root_output/generation_${src_mm100_lang_code}_${TRG_MM100_LANG_CODE}"

      # clean fairseq generated file to only create hypotheses file.
      grep -P '^H-' "$root_output/generation_${src_mm100_lang_code}_${TRG_MM100_LANG_CODE}/generate-train.txt" |
        cut -c 3- |
        sort -n -k 1 |
        awk -F "\t" '{print $NF}' \
          >"$root_output/generation_${src_mm100_lang_code}_${TRG_MM100_LANG_CODE}/${TRG_LANG_CODE}.txt"
    done
  done
done
