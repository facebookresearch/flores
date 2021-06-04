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
from tempfile import NamedTemporaryFile as TempFile
import time
import subprocess
import multiprocessing as mp
from utils import check_last_line, count_line
import tqdm


def translate_files_slurm(args, cmds, expected_output_files):
    conda_env = '/private/home/pipibjc/.conda/envs/fairseq-20190509'
    for cmd in cmds:
        with TempFile('w') as script:
            sh = f"""#!/bin/bash
            source activate {conda_env}
            {cmd}
            """
            print(sh)
            script.write(sh)
            script.flush()
            cmd = f"sbatch --gres=gpu:1 -c {args.cpu + 2} {args.sbatch_args} --time=15:0:0 {script.name}"
            import sys
            print(cmd, file=sys.stderr)
            check_call(cmd, shell=True)

    # wait for all outputs has finished
    num_finished = 0
    while num_finished < len(expected_output_files):
        num_finished = 0
        for output_file in expected_output_files:
            num_finished += 1 if check_finished(output_file) else 0
        if num_finished < len(expected_output_files):
            time.sleep(3 * 60)
            print("sleeping for 3m ...")


def check_finished(output_file):
    return check_last_line(output_file, "finished")


def get_output_file(dest_dir, file):
    return f"{dest_dir}/{os.path.basename(file)}.log"


def translate(arg_list):
    (q, cmd) = arg_list
    i = q.get()
    os.environ['CUDA_VISIBLE_DEVICES']=str(i)
    cmd = f"CUDA_VISIBLE_DEVICES={i} {cmd}"
    print(f"executing:\n{cmd}")
    check_call(cmd, shell=True)
    q.put(i)


def translate_files_local(args, cmds):
    m = mp.Manager()
    gpu_queue = m.Queue()
    for i in args.cuda_visible_device_ids:
        gpu_queue.put(i)
    with mp.Pool(processes=len(args.cuda_visible_device_ids)) as pool:
        for _ in tqdm.tqdm(pool.imap_unordered(translate, [(gpu_queue, cmd) for cmd in cmds]), total=len(cmds)):
            pass


def translate_files(args, dest_dir, input_files):
    cmd_template = f"""fairseq-interactive \
        {args.databin} \
        --source-lang {args.source_lang} --target-lang {args.target_lang} \
        --path {args.model} \
        --lenpen {args.lenpen} \
        --max-len-a {args.max_len_a} \
        --max-len-b {args.max_len_b} \
        --buffer-size {args.buffer_size} \
        --max-tokens {args.max_tokens} \
        --num-workers {args.cpu} > {{output_file}} && \
    echo "finished" >> {{output_file}}
    """
    cmds = []
    expected_output_files = []
    for input_file in input_files:
        output_file = get_output_file(dest_dir, input_file)
        cmds.append(f"cat {input_file} | " + cmd_template.format(output_file=output_file))
        expected_output_files.append(output_file)
    if args.backend == 'local':
        translate_files_local(args, cmds)
    elif args.backend == 'slurm':
        translate_files_slurm(args, cmds, expected_output_files)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', '-d', required=True, help='Path to file to translate')
    parser.add_argument('--model', '-m', required=True, help='Model checkpoint')
    parser.add_argument('--lenpen', default=1.2, type=float, help='Length penalty')
    parser.add_argument('--beam', default=5, type=int, help='Beam size')
    parser.add_argument('--max-len-a', type=float, default=0, help='max-len-a parameter when back-translating')
    parser.add_argument('--max-len-b', type=int, default=200, help='max-len-b parameter when back-translating')
    parser.add_argument('--cpu', type=int, default=4, help='Number of CPU for interactive.py')
    parser.add_argument('--cuda-visible-device-ids', '-gids', default=None, nargs='*', help='List of cuda visible devices ids, camma separated')
    parser.add_argument('--dest', help='Output path for the intermediate and translated file')
    parser.add_argument('--max-tokens', type=int, default=12000, help='max tokens')
    parser.add_argument('--buffer-size', type=int, default=10000, help='Buffer size')
    parser.add_argument('--chunks', type=int, default=100)
    parser.add_argument('--source-lang', type=str, default=None, help='Source langauge. Will inference from the model if not set')
    parser.add_argument('--target-lang', type=str, default=None, help='Target langauge. Will inference from the model if not set')
    parser.add_argument('--databin', type=str, default=None, help='Parallel databin. Will combine with the back-translated databin')
    parser.add_argument('--sbatch-args', default='', help='Extra SBATCH arguments')

    parser.add_argument('--backend', type=str, default='local', choices=['local', 'slurm'])
    args = parser.parse_args()

    args.cuda_visible_device_ids = args.cuda_visible_device_ids or list(range(torch.cuda.device_count()))

    chkpnt = torch.load(args.model)
    model_args = chkpnt['args']
    if args.source_lang is None or args.target_lang is None:
        args.source_lang = args.source_lang or model_args.source_lang
        args.target_lang = args.target_lang or model_args.target_lang
    if args.databin is None:
        args.databin = args.databin or model_args.data

    root_dir = os.path.dirname(os.path.realpath(__file__))
    translation_dir = os.path.join(args.dest or root_dir, 'translations', f'{args.source_lang}-{args.target_lang}')

    tempdir = os.path.join(translation_dir, 'splits')
    os.makedirs(tempdir, exist_ok=True)
    split_files = glob(f'{tempdir}/mono_data*')

    if len(split_files) != args.chunks:
        if len(split_files) != 0:
            print("number of split files are not the same as chunks. removing files and re-split")
            [os.remove(os.path.join(tempdir, f)) for f in os.listdir(tempdir)]
        print("splitting files ...")
        check_call(f'split -n "r/{args.chunks}" -a3 -d {args.data} {tempdir}/mono_data', shell=True)
        split_files = glob(f'{tempdir}/mono_data*')
    else:
        print("has the same number of splitted file and the specified chunks, skip splitting file")

    translated_files = []
    files_to_translate = []
    for file in split_files:
        # skip the translation job if it's finished
        output_file = get_output_file(translation_dir, file)
        translated_files.append(output_file)
        if check_finished(output_file):
            print(f"{output_file} is translated")
            continue
        files_to_translate.append(file)

    print(f"{len(files_to_translate)} files to translate")

    translate_files(args, translation_dir, files_to_translate)

    # aggregate translated files
    generated_src = f'{args.dest}/generated.src'
    generated_tgt = f'{args.dest}/generated.hypo'
    if count_line(generated_src) != count_line(generated_tgt) or count_line(generated_src) <= 0:
        print(f"aggregating translated {len(translated_files)} files")
        with TempFile() as fout:
            files = " ".join(translated_files)
            check_call(f"cat {files}", shell=True, stdout=fout)
            # strip head and make pairs
            check_call(f'cat {fout.name} | grep "^S" | cut -f2 > {generated_src}', shell=True)
            check_call(f'cat {fout.name} | grep "^H" | cut -f3 > {generated_tgt}', shell=True)
    assert count_line(generated_src) == count_line(generated_tgt)
    print(f"output generated files to {generated_src}, {generated_tgt}")


if __name__ == '__main__':
    main()
