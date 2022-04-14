#!/bin/bash

fairseq='/private/home/oignat/fairseq'
flores101_dataset='/private/home/oignat/flores101_dataset'

declare -A lang_codes=( ["npi"]="ne")
# SRC_LANG_CODE=npi
TRG_LANG_CODE=eng

# SRC_MM100_LANG_CODE=ne
TRG_MM100_LANG_CODE=en

for data_type in books_10k books_20k books_30k;
do
    for SRC_LANG_CODE in "${!lang_codes[@]}";
    do 
        root_output='/checkpoint/oignat/Data/backtranslation/data_books/'${data_type}    
        mkdir -p $root_output/SPM/mono/
        echo $root_output
         
        SRC_MM100_LANG_CODE="${lang_codes[${SRC_LANG_CODE}]}"
        if [ ! -f $root_output/${SRC_LANG_CODE}_mono.txt ]; then
            echo $root_output/${SRC_LANG_CODE}_mono.txt doesnt exist
            continue
        fi
        generation_file=$root_output/generation_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE}/${TRG_LANG_CODE}.txt
        echo ${SRC_LANG_CODE} ${SRC_MM100_LANG_CODE}
        if [ -s "${generation_file}" ] && [ "$(wc -l < ${generation_file})" -eq 10000 ]; then
            echo "${generation_file} exists and has 10000 lines."
            continue
        else
            echo "$generation_file doesn't exist or hasn't 10000 lines"   
        fi
        python $fairseq/scripts/spm_encode.py \
            --model $fairseq/flores101_mm100_615M/sentencepiece.bpe.model \
            --output_format=piece \
            --inputs=$root_output/${SRC_LANG_CODE}_mono.txt \
            --outputs=$root_output/SPM/mono/spm.${SRC_MM100_LANG_CODE}-${TRG_MM100_LANG_CODE}.${SRC_MM100_LANG_CODE}

        python $fairseq/scripts/spm_encode.py \
            --model $fairseq/flores101_mm100_615M/sentencepiece.bpe.model \
            --output_format=piece \
            --inputs=$root_output/${SRC_LANG_CODE}_mono.txt \
            --outputs=$root_output/SPM/mono/spm.${SRC_MM100_LANG_CODE}-${TRG_MM100_LANG_CODE}.${TRG_MM100_LANG_CODE}

        fairseq-preprocess \
            --source-lang ${SRC_MM100_LANG_CODE} --target-lang ${TRG_MM100_LANG_CODE} \
            --trainpref $root_output/SPM/mono/spm.${SRC_MM100_LANG_CODE}-${TRG_MM100_LANG_CODE} \
            --thresholdsrc 0 --thresholdtgt 0 \
            --destdir $root_output/data_bin_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE} \
            --srcdict $fairseq/flores101_mm100_615M/dict.txt --tgtdict $fairseq/flores101_mm100_615M/dict.txt

        fairseq-generate \
            $root_output/data_bin_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE} \
            --batch-size 256 \
            --skip-invalid-size-inputs-valid-test \
            --path $fairseq/flores101_mm100_615M/model.pt \
            --fixed-dictionary $fairseq/flores101_mm100_615M/dict.txt \
            -s ${SRC_MM100_LANG_CODE} -t ${TRG_MM100_LANG_CODE} \
            --remove-bpe 'sentencepiece' \
            --beam 5 \
            --fp16 \
            --task translation_multi_simple_epoch \
            --lang-pairs $fairseq/flores101_mm100_615M/language_pairs.txt \
            --decoder-langtok --encoder-langtok src \
            --gen-subset train \
            --dataset-impl mmap \
            --distributed-world-size 1 --distributed-no-spawn \
            --results-path $root_output/generation_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE}

        # # # clean fairseq generated file to only create hypotheses file.
        cat $root_output/generation_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE}/generate-train.txt  | grep -P '^H-'  | cut -c 3- | sort -n -k 1 | awk -F "\t" '{print $NF}' > $root_output/generation_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE}/${TRG_LANG_CODE}.txt
    done
done

