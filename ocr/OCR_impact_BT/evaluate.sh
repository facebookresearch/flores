#!/bin/bash

fairseq='/private/home/oignat/fairseq'
flores101_dataset='/private/home/oignat/flores101_dataset'
CHECKPOINT_IN='/private/home/oignat/fairseq/flores101_mm100_615M/model.pt'

declare -A lang_codes=( ["pus"]="ps" ["jpn"]="ja" ["khm"]="km" ["tam"]="ta" ["amh"]="am" ["lao"]="lo" ["npi"]="ne")

# eng -> npi
SRC_LANG_CODE=eng
# TRG_LANG_CODE=npi
SRC_MM100_LANG_CODE=en
# TRG_MM100_LANG_CODE=ne

for TRG_LANG_CODE in "${!lang_codes[@]}";
do
    for error_rate in {1..32..2};
    do
        for error_type in insert delete replace;
        do
            data_type=${error_rate}/${error_type}
            root_output='/private/home/oignat/flores_OCR/Data/backtranslation/data_cer_20k/'${data_type}    
            root_CHECKPOINT_OUT=${root_output}'/model_checkpoints'
            TRG_MM100_LANG_CODE="${lang_codes[${TRG_LANG_CODE}]}"
            CHECKPOINT_OUT=${root_CHECKPOINT_OUT}_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE}
            echo ${CHECKPOINT_OUT}

            if [ -f "$CHECKPOINT_OUT/checkpoint6.pt" ];
            then 
                echo "$CHECKPOINT_OUT/checkpoint6.pt exists"
                if [ -s $root_output/generation_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE}/${TRG_LANG_CODE}.txt ];
                then
                    echo "here"
                    echo "${data_type} ${TRG_LANG_CODE}" >> "/private/home/oignat/flores_OCR/Data/backtranslation/data_cer_20k/results3.txt"
                    ## Evaluate
                    sacrebleu $flores101_dataset/devtest/${TRG_LANG_CODE}.devtest < $root_output/generation_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE}/${TRG_LANG_CODE}.txt --tokenize spm >> /private/home/oignat/flores_OCR/Data/backtranslation/data_cer_20k/results3.txt
                else
                    echo "there"
                    echo $root_output/generation_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE}/${TRG_LANG_CODE}.txt doesnt exist
                fi
            fi
        done
    done
done