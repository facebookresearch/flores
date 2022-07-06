#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

import argparse
import os
import torch
from subprocess import check_call, check_output
from glob import glob
from tempfile import TemporaryDirectory, NamedTemporaryFile as TempFile
import math
import json
from utils import check_last_line


def read_config(config_path):
    with open(config_path, 'r') as js:
        return json.load(js)


def call(cmd, shell=True):
    print(cmd)
    check_call(cmd, shell=shell)

def train(src, tgt, train_config, savedir, databin):
    # expect to have 'hyperparameters', 'src', 'tgt', 'databin' in train_config
    os.makedirs(savedir, exist_ok=True)

    logpath = os.path.join(savedir, 'train.log')
    checkpoint = os.path.join(savedir, 'checkpoint_best.pt')

    if check_last_line(logpath, 'done') and os.path.exists(checkpoint):
        print(f"Training is finished. Best checkpoint: {checkpoint}")
        return

    cuda_visible_devices = list(range(torch.cuda.device_count()))
    num_visible_gpu = len(cuda_visible_devices)
    num_gpu = min(train_config['gpu'], 2**int(math.log2(num_visible_gpu)))
    cuda_devices_clause = f"CUDA_VISIBLE_DEVICES={','.join([str(i) for i in cuda_visible_devices[:num_gpu]])}"
    update_freq = train_config['gpu'] / num_gpu
    call(f"""{cuda_devices_clause} fairseq-train {databin} \
        --source-lang {src} --target-lang {tgt} \
        --save-dir {savedir} \
        --update-freq {update_freq} \
        {" ".join(train_config['parameters'])} \
        | tee {logpath}
    """, shell=True)


def eval_bleu(src, tgt, subset, lenpen, databin, checkpoint, output, max_token=20000):
    bleuarg = "--sacrebleu" if tgt == "en" else ""
    call(f"""fairseq-generate {databin} \
        --source-lang {src} --target-lang {tgt} \
        --path {checkpoint} \
        --max-tokens {max_token} \
        --beam 5 \
        --lenpen {lenpen} \
        --max-len-a 1.8 \
        --max-len-b 10 \
        --gen-subset {subset} \
        --remove-bpe=sentencepiece \
        {bleuarg} > {output}
    """)
    return check_output(f"tail -n 1 {output}", shell=True).decode('utf-8').strip()


def translate(src, tgt, model, lenpen, dest, data, max_token=12000):
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'translate.py')
    check_call(f"""python {script_path} --data {data}\
        --source-lang {src} --target-lang {tgt} \
        --model {model} \
        --beam 5 --lenpen {lenpen} \
        --max-len-a 1.8 \
        --max-len-b 10 \
        --dest {dest} \
        --max-token {max_token} \
        --chunks 100 \
        --backend local
    """, shell=True)

# (src, tgt) is the direction of the databin
def build_bt_databin(src, tgt, train_prefix, para_databin, output_folder):
    final_output = os.path.join(f'{output_folder}/data-bin')
    if os.path.exists(final_output):
        print(f"Databin path {final_output} exists")
        return final_output

    train_databin = os.path.join(output_folder, 'train-data-bin')
    os.makedirs(train_databin, exist_ok=True)
    call(f"ln -fs {train_prefix}.hypo {output_folder}/bt.{src}")
    call(f"ln -fs {train_prefix}.src {output_folder}/bt.{tgt}")

    call(f"""fairseq-preprocess \
        --source-lang {src} --target-lang {tgt} \
        --trainpref {output_folder}/bt \
        --destdir {train_databin} \
        --joined-dictionary \
        --srcdict {para_databin}/dict.{src}.txt \
        --workers 40
    """)

    os.makedirs(final_output, exist_ok=True)
    call(f"ln -fs {para_databin}/* {final_output}")
    for lang in [src, tgt]:
        for suffix in ['idx', 'bin']:
            file_suffix = f"{src}-{tgt}.{lang}.{suffix}"
            call(f"ln -fs {train_databin}/train.{file_suffix} {output_folder}/data-bin/train1.{file_suffix}")
    return final_output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', required=True, help='pipeline config')
    parser.add_argument('--databin', '-d', required=True, help='initial databin')
    args = parser.parse_args()

    configs = read_config(args.config)
    workdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../experiments')
    #cuda_visible_devices=args.cuda_visible_devices or list(range(torch.cuda.device_count()))

    initial_databin = args.databin
    for i in range(len(configs)):
        (name, config) = configs[i]
        src = config['src']
        tgt = config['tgt']
        direction = f"{src}-{tgt}"
        print(f"Start {name} iteration, {direction}")
        iter_workdir = os.path.join(workdir, name, direction)
        # train
        model_dir = os.path.join(iter_workdir, 'model')
        train(src, tgt, config['train'], model_dir, initial_databin)
        checkpoint_path = os.path.join(model_dir, 'checkpoint_best.pt')
        # eval
        lenpen = config['translate']['lenpen']
        eval_output = os.path.join(model_dir, 'eval.txt')
        if check_last_line(eval_output, "BLEU"):
            print(check_output(f"tail -n 1 {eval_output}", shell=True).decode('utf-8').strip())
        else:
            print(eval_bleu(
                config['src'], config['tgt'],
                'test', lenpen,
                args.databin, checkpoint_path,
                os.path.join(model_dir, 'eval.txt')
            ))
        # Early exit to skip back-translation for the last iteration
        if i == len(configs) - 1:
            break
        # translate
        translate_output = os.path.join(iter_workdir, 'synthetic')
        translate(config['src'], config['tgt'], checkpoint_path, lenpen, translate_output, config['translate']['mono'], config['translate']['max_token'])
        # generate databin
        databin_folder = os.path.join(translate_output, 'bt')
        initial_databin = build_bt_databin(
            config['tgt'], config['src'],
            os.path.join(translate_output, 'generated'), args.databin, databin_folder
        )

main()
