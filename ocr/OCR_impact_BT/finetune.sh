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
    for error_rate in {1..32..6};
    do
        for error_type in insert delete replace;
        do
            data_type=${error_rate}/${error_type}
            root_output='/private/home/oignat/flores_OCR/Data/backtranslation/data_cer_20k/'${data_type}    
            root_CHECKPOINT_OUT=${root_output}'/model_checkpoints'
            TENSORBOARD_LOG_DIR=${root_output}'/logdir'
            LOG_FILE='/private/home/oignat/flores_OCR/Data/backtranslation/data_cer_20k/logs.txt'

            mkdir -p $root_output/SPM/train/
            mkdir -p $root_output/SPM/test/
            mkdir -p $root_output/SPM/val/
          
            TRG_MM100_LANG_CODE="${lang_codes[${TRG_LANG_CODE}]}"
            echo ${TRG_LANG_CODE} ${TRG_MM100_LANG_CODE}
            if [ ! -s $root_output/generation_${TRG_MM100_LANG_CODE}_${SRC_MM100_LANG_CODE}/${SRC_LANG_CODE}.txt ];
            then
                echo $root_output/generation_${TRG_MM100_LANG_CODE}_${SRC_MM100_LANG_CODE}/${SRC_LANG_CODE}.txt doesnt exist
                continue
            fi
            CHECKPOINT_OUT=${root_CHECKPOINT_OUT}_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE}
            echo ${CHECKPOINT_OUT}
            if [ -f "$CHECKPOINT_OUT/checkpoint6.pt" ];
            then 
                echo "$CHECKPOINT_OUT/checkpoint6.pt exists"
            else
                echo "$CHECKPOINT_OUT/checkpoint6.pt doesn't exist!"

                python $fairseq/scripts/spm_encode.py \
                    --model $fairseq/flores101_mm100_615M/sentencepiece.bpe.model \
                    --output_format=piece \
                    --inputs=$root_output/generation_${TRG_MM100_LANG_CODE}_${SRC_MM100_LANG_CODE}/${SRC_LANG_CODE}.txt \
                    --outputs=$root_output/SPM/train/spm.${SRC_MM100_LANG_CODE}-${TRG_MM100_LANG_CODE}.${SRC_MM100_LANG_CODE}

                python $fairseq/scripts/spm_encode.py \
                    --model $fairseq/flores101_mm100_615M/sentencepiece.bpe.model \
                    --output_format=piece \
                    --inputs=$root_output/${TRG_LANG_CODE}_mono.txt \
                    --outputs=$root_output/SPM/train/spm.${SRC_MM100_LANG_CODE}-${TRG_MM100_LANG_CODE}.${TRG_MM100_LANG_CODE}

                python $fairseq/scripts/spm_encode.py \
                    --model $fairseq/flores101_mm100_615M/sentencepiece.bpe.model \
                    --output_format=piece \
                    --inputs=$flores101_dataset/dev/${SRC_LANG_CODE}.dev \
                    --outputs=$root_output/SPM/val/spm.${SRC_MM100_LANG_CODE}-${TRG_MM100_LANG_CODE}.${SRC_MM100_LANG_CODE}

                python $fairseq/scripts/spm_encode.py \
                    --model $fairseq/flores101_mm100_615M/sentencepiece.bpe.model \
                    --output_format=piece \
                    --inputs=$flores101_dataset/dev/${TRG_LANG_CODE}.dev \
                    --outputs=$root_output/SPM/val/spm.${SRC_MM100_LANG_CODE}-${TRG_MM100_LANG_CODE}.${TRG_MM100_LANG_CODE}

                python $fairseq/scripts/spm_encode.py \
                    --model $fairseq/flores101_mm100_615M/sentencepiece.bpe.model \
                    --output_format=piece \
                    --inputs=$flores101_dataset/devtest/${SRC_LANG_CODE}.devtest \
                    --outputs=$root_output/SPM/test/spm.${SRC_MM100_LANG_CODE}-${TRG_MM100_LANG_CODE}.${SRC_MM100_LANG_CODE}

                python $fairseq/scripts/spm_encode.py \
                    --model $fairseq/flores101_mm100_615M/sentencepiece.bpe.model \
                    --output_format=piece \
                    --inputs=$flores101_dataset/devtest/${TRG_LANG_CODE}.devtest \
                    --outputs=$root_output/SPM/test/spm.${SRC_MM100_LANG_CODE}-${TRG_MM100_LANG_CODE}.${TRG_MM100_LANG_CODE}

                # #### Binarization
                fairseq-preprocess \
                    --source-lang ${SRC_MM100_LANG_CODE} --target-lang ${TRG_MM100_LANG_CODE} \
                    --validpref $root_output/SPM/val/spm.${SRC_MM100_LANG_CODE}-${TRG_MM100_LANG_CODE} \
                    --trainpref $root_output/SPM/train/spm.${SRC_MM100_LANG_CODE}-${TRG_MM100_LANG_CODE} \
                    --testpref $root_output/SPM/test/spm.${SRC_MM100_LANG_CODE}-${TRG_MM100_LANG_CODE} \
                    --thresholdsrc 0 --thresholdtgt 0 \
                    --destdir $root_output/data_bin_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE} \
                    --srcdict $fairseq/flores101_mm100_615M/dict.txt --tgtdict $fairseq/flores101_mm100_615M/dict.txt
            
                lang_pairs="${SRC_MM100_LANG_CODE}-${TRG_MM100_LANG_CODE}"
                fairseq-train --fp16 \
                    --memory-efficient-fp16 \
                    $root_output/data_bin_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE} \
                    --finetune-from-model ${CHECKPOINT_IN} \
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
                    --source-lang ${SRC_MM100_LANG_CODE} --target-lang ${TRG_MM100_LANG_CODE} \
                    --update-freq 2 \
                    --seed 2 \
                    --max-source-positions 1024 --max-target-positions 1024 \
                    --max-epoch 6 --save-interval 3 \
                    --tensorboard-logdir ${TENSORBOARD_LOG_DIR} \
                    --save-dir ${CHECKPOINT_OUT} \
                    --log-file ${LOG_FILE}
                
                python -c "import torch; torch.cuda.empty_cache()"
            fi
            
            if [ -s $root_output/generation_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE}/${TRG_LANG_CODE}.txt ];
            then 
                echo $root_output/generation_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE}/${TRG_LANG_CODE}.txt exists
            else
                echo $root_output/generation_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE}/${TRG_LANG_CODE}.txt doesnt exist
            
                fairseq-generate \
                    $root_output/data_bin_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE} \
                    --batch-size 512 \
                    --path ${CHECKPOINT_OUT}/checkpoint_best.pt  \
                    --fixed-dictionary $fairseq/flores101_mm100_615M/dict.txt \
                    -s ${SRC_MM100_LANG_CODE} -t ${TRG_MM100_LANG_CODE} \
                    --remove-bpe 'sentencepiece' \
                    --beam 5 \
                    --task translation_multi_simple_epoch \
                    --lang-pairs $fairseq/flores101_mm100_615M/language_pairs.txt \
                    --decoder-langtok --encoder-langtok src \
                    --gen-subset test \
                    --fp16 \
                    --dataset-impl mmap \
                    --distributed-world-size 1 --distributed-no-spawn \
                    --results-path $root_output/generation_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE} 
            fi
            
            if [ -s $root_output/generation_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE}/generate-test.txt ];
            then
                ## clean fairseq generated file to only create hypotheses file.
                cat $root_output/generation_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE}/generate-test.txt  | grep -P '^H-'  | cut -c 3- | sort -n -k 1 | awk -F "\t" '{print $NF}' > $root_output/generation_${SRC_MM100_LANG_CODE}_${TRG_MM100_LANG_CODE}/${TRG_LANG_CODE}.txt
            fi
        
        done
    done
done