#!/usr/bin/env bash

if [[ -z "$flores101_dataset" ]]; then
  echo 'Need to specify the env var flores101_dataset.'
  exit 1
fi

source OCR_impact_BT/lang_codes.source

SRC_MM100_LANG_CODE=en

SIZE=20k

for trg_lang_code in "${!LANG_CODES[@]}"; do
    for error_rate in {1..22..2}; do
        for error_type in insert delete replace; do
            data_type=${error_rate}/${error_type}
            root_output="Data/backtranslation/data_cer_$SIZE/${data_type}"
            root_checkpoint_out="${root_output}/model_checkpoints"
            trg_m100_lang_code="${LANG_CODES[${trg_lang_code}]}"
            checkpoint_out=${root_checkpoint_out}_${SRC_MM100_LANG_CODE}_${trg_m100_lang_code}
            if [ -f "$checkpoint_out/checkpoint6.pt" ]; then
                if [ -s "$root_output/generation_${SRC_MM100_LANG_CODE}_${trg_m100_lang_code}/${trg_lang_code}.txt" ]; then
                    echo "${data_type} ${trg_lang_code}" >> "Data/backtranslation/data_cer_$SIZE/results3.txt"
                    sacrebleu \
                      "${flores101_dataset}/devtest/${trg_lang_code}.devtest" \
                      < "$root_output/generation_${SRC_MM100_LANG_CODE}_${trg_m100_lang_code}/${trg_lang_code}.txt" \
                      --tokenize spm >> "Data/backtranslation/data_cer_$SIZE/results3.txt"
                else
                    echo "$root_output/generation_${SRC_MM100_LANG_CODE}_${trg_m100_lang_code}/${trg_lang_code}.txt" doesn\'t exist
                fi
            fi
        done
    done
done
