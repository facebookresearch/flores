#!/usr/bin/env python
import argparse
import csv
import os
import sys
import unicodedata
from collections import Counter
from itertools import product
from random import sample
from statistics import mean

import Levenshtein
import editdistance as ed
import pandas as pd
import tqdm

from data_collection.utils import create_dictionary_lang

lang_code_dict = create_dictionary_lang()


def prep_data_for_backtranslation():
    DATA = "UDHR"
    for lang_code in ['khm', 'lao', 'npi', 'pbu', 'tam']:
        lang_name = lang_code_dict[lang_code]
        root_lang_name = "Data/" + DATA + "/" + lang_name + "/"

        file_names_GT = []
        file_names_pred = []
        for i in range(1, 31):
            name_img = lang_code + str(i)
            groundtruth_split_input = root_lang_name + name_img + "_split.txt"
            predicted_split_output = root_lang_name + "googlevision/" + name_img + "_sentsplit.txt"
            if not os.path.exists(predicted_split_output):
                continue
            file_names_GT.append(groundtruth_split_input)
            file_names_pred.append(predicted_split_output)

        os.makedirs("Data/backtranslation", exist_ok=True)
        with open("Data/backtranslation/" + DATA + "_" + lang_code + "_GT.txt", "w") as outfile:
            for path in file_names_GT:
                with open(path) as file:
                    outfile.write(file.read() + "\n")

        with open("Data/backtranslation/" + DATA + "_" + lang_code + "_OCR.txt", "w") as outfile:
            for path in file_names_pred:
                with open(path) as file:
                    outfile.write(file.read() + "\n")


def extract_OCR_errors(GT_input, OCRed_input):
    with open(OCRed_input, encoding="utf8") as f:
        input_txt_ocr = f.readlines()
    with open(GT_input, encoding="utf8") as f:
        input_txt = f.readlines()

    all_list_operations = {'insert': [], 'delete': [], 'replace': []}

    for i in tqdm.tqdm(range(len(input_txt_ocr))):
        groundtruth_split_input_part = unicodedata.normalize('NFC',
                                                             input_txt[i].replace('\u200d', '').replace('\u200c', ''))
        OCRed_split_output_part = unicodedata.normalize('NFC',
                                                        input_txt_ocr[i].replace('\u200d', '').replace('\u200c', ''))

        seq1 = groundtruth_split_input_part
        seq2 = OCRed_split_output_part
        list_operation_names = [(op, seq1[idx1], seq2[idx2]) for (op, idx1, idx2) in Levenshtein.editops(seq1, seq2)]
        for l in list_operation_names:
            if l[0] == 'insert':
                all_list_operations[l[0]].append(l[2])
            elif l[0] == 'delete':
                all_list_operations[l[0]].append(l[1])
            elif l[0] == 'replace':
                all_list_operations[l[0]].append((l[1], l[2]))

    for key, value in all_list_operations.items():
        all_list_operations[key] = Counter(value).most_common(10)
    print("OCR Errors:" + all_list_operations)
    return all_list_operations


def measure_ocr_error_rate(ocr_input_path: str, gt_input_path: str) -> None:
    with open(ocr_input_path, encoding="utf8") as file:
        input_txt_ocr = file.readlines()
    with open(gt_input_path, encoding="utf8") as file:
        input_txt = file.readlines()

    print(len(input_txt_ocr))
    print(len(input_txt))
    list_cer = []
    list_wer = []
    for i in tqdm.tqdm(range(0, 10000, 1000)):
        groundtruth_split_input_part = input_txt[i:i + 1000]
        OCRed_split_output_part = input_txt_ocr[i:i + 1000]
        OCRed_split_output_part = " ".join(s.strip() for s in OCRed_split_output_part)
        groundtruth_split_input_part = " ".join(s.strip() for s in groundtruth_split_input_part)

        if groundtruth_split_input_part and OCRed_split_output_part:
            cer = ed.eval(OCRed_split_output_part, groundtruth_split_input_part) / float(
                len(groundtruth_split_input_part))
            wer = ed.eval(OCRed_split_output_part.split(), groundtruth_split_input_part.split()) / float(
                len(groundtruth_split_input_part.split()))
            list_cer.append(cer * 100)
            list_wer.append(wer * 100)
            print("{:.2f}".format(cer * 100) + "," + "{:.2f}".format(wer * 100))
            break
        else:
            print(i, "sth wrong", len(OCRed_split_output_part), len(groundtruth_split_input_part))

    print("{:.2f}".format(mean(list_cer)) + "," + "{:.2f}".format(mean(list_wer)))


def read_monolingual_data(lang_code: str, size: str = "10k", threshold: float = 1.03) -> None:
    if size == "10k":
        max_lines = 10000
    elif size == "20k":
        max_lines = 20000
    else:
        raise ValueError(f"Illegal size value: {size}")

    max_words = 40
    dict_codes_cc100 = {"amh": "am", "pus": "ps", "khm": "km", "lao": "lo"}
    dict_codes_wikimatrix = {"npi": "en-ne", "jpn": "en-ja", "tam": "en-ta", "ron": "en-ro"}
    csv.field_size_limit(sys.maxsize)

    mono = []
    if lang_code in dict_codes_cc100:
        with open("Data/MONOLINGUAL/CC100." + dict_codes_cc100[lang_code] + ".txt", encoding="utf8") as f:
            data = f.readlines()
        data = [i for i in data if i.strip() and len(i.split()) <= max_words]  # remove empty lines
        mono = data[:max_lines]

    elif lang_code in dict_codes_wikimatrix:
        with open("Data/MONOLINGUAL/WikiMatrix." + dict_codes_wikimatrix[lang_code] + ".tsv",
                  encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, delimiter='\t', quoting=csv.QUOTE_NONE)
            for row in reader:
                if float(row[0]) > threshold and len(row) == 3 and row[2] and len(row[2].split()) <= max_words and (
                        row[1] not in row[2]) and (row[2] not in row[1]):
                    mono.append(row[2])
                    if len(mono) == max_lines:
                        break
    else:
        raise ValueError("Error: No " + lang_code + "in dict_codes_cc100 or dict_codes_wikimatrix")

    if max_lines == 20000:
        path_output = "Data/MONOLINGUAL/20k/"
    elif max_lines == 100000:
        path_output = "Data/MONOLINGUAL/100k/"
    elif max_lines == 10000:
        path_output = "Data/MONOLINGUAL/10k/"
    else:
        raise ValueError("max lines unknown: " + str(max_lines))
    os.makedirs(path_output, exist_ok=True)

    print(len(mono))
    with open(path_output + lang_code + "_mono.txt", "w") as fout:
        for line in mono:
            print(line.strip(), file=fout)


def find(s, ch):
    return [i for i, ltr in enumerate(s) if ltr == ch]


def delete_multiple_element(list_object, indices):
    indices = sorted(indices, reverse=True)
    for idx in indices:
        if idx < len(list_object):
            list_object.pop(idx)
    return list_object


def insert_multiple_element(list_object, indices, char):
    indices = sorted(indices, reverse=True)
    for idx in indices:
        if idx < len(list_object):
            list_object.insert(idx, char)
    return list_object


def add_replacement_errors(all_error_types, all_mono, error_rate):
    nb_total_replaces = round(error_rate * len(all_mono) / 100)
    nb_replaces_per_char = round(nb_total_replaces / len(all_error_types['replace']))

    for ((char1, char2), freq) in all_error_types['replace']:
        all_char1_indices = find(all_mono, char1)
        k = nb_replaces_per_char
        if len(all_char1_indices) < k:
            k = len(all_char1_indices)

        randomly_sampled_indices = sample(range(len(all_char1_indices)), int(k))
        randomly_sampled_indices_real = [all_char1_indices[idx] for idx in randomly_sampled_indices]
        for idx in randomly_sampled_indices_real:
            all_mono = all_mono[0:idx] + char2 + all_mono[idx + 1:]
    return all_mono


def add_deletion_errors(all_error_types, all_mono, error_rate):
    nb_total_deletions = round(error_rate * len(all_mono) / 100)
    nb_deletions_per_char = nb_total_deletions // len(all_error_types['delete'])

    for (char, freq) in all_error_types['delete']:
        all_char_indices = find(all_mono, char)
        k = nb_deletions_per_char
        if len(all_char_indices) < k:
            k = len(all_char_indices)
        randomly_sampled_indices = sample(range(len(all_char_indices)), int(k))
        randomly_sampled_indices_real = [all_char_indices[idx] for idx in randomly_sampled_indices]
        all_mono = delete_multiple_element(list(all_mono), randomly_sampled_indices_real)
    return "".join(all_mono)


def add_insertion_errors(all_error_types, all_mono, error_rate):
    nb_total_insertions = round(error_rate * len(all_mono) / 100)
    nb_insertions_per_char = nb_total_insertions // len(all_error_types['insert'])

    for (char, freq) in all_error_types['insert']:
        k = nb_insertions_per_char
        randomly_sampled_indices_real = sample(range(len(all_mono)), int(k))
        all_mono = insert_multiple_element(list(all_mono), randomly_sampled_indices_real, char)
    return "".join(all_mono)


def write_error_rate(all_mono_ocred, all_mono, path_output, lang_code: str, size) -> None:
    cer = ed.eval(all_mono_ocred, all_mono) / float(len(all_mono))
    wer = ed.eval(all_mono_ocred.split(), all_mono.split()) / float(len(all_mono.split()))
    cer_wer = path_output + "/replace/" + lang_code + "_mono.txt" + " " + str(cer * 100) + " " + str(wer * 100)
    with open("Data/backtranslation/data_cer_" + size + "/" + "error_rates.txt", 'a') as f:
        f.write(cer_wer + "\n")


def introduce_errors_in_monolingual(all_error_types, lang_code, error_rate, size):
    if size == "10k":
        data_size = 10001
    elif size == "20k":
        data_size = 20001
    else:
        raise ValueError("size param can only be 10k or 20k for now")
    path_input = "Data/MONOLINGUAL/" + size + "/"
    path_output = "Data/backtranslation/data_cer_" + size + "/" + str(error_rate)

    os.makedirs(path_output, exist_ok=True)
    os.makedirs(path_output + "/replace/", exist_ok=True)
    os.makedirs(path_output + "/insert/", exist_ok=True)
    os.makedirs(path_output + "/delete/", exist_ok=True)

    with open(path_input + lang_code + "_mono.txt", encoding="utf8") as f:
        mono = f.readlines()

        # add replacement errors in all_mono data and write the error rate results in file
    all_mono = " ".join(mono)
    if lang_code != 'jpn':
        if os.path.isfile(path_output + "/replace/" + lang_code + "_mono.txt") and sum(
                1 for _ in open(path_output + "/replace/" + lang_code + "_mono.txt")) == data_size:
            print(path_output + "/replace/" + lang_code + "_mono.txt exists and has " + str(data_size) + " lines")
        else:
            all_mono_ocred = add_replacement_errors(all_error_types, all_mono, error_rate)
            with open(path_output + "/replace/" + lang_code + "_mono.txt", "w") as fout:
                print(all_mono_ocred, file=fout)
            write_error_rate(all_mono_ocred, all_mono, path_output, lang_code, size)

    # add deletion errors in all_mono data and write the error rate results in file
    all_mono = " ".join(mono)
    if lang_code != 'jpn':
        if not all_error_types['delete']:
            all_mono_ocred = all_mono
            with open(path_output + "/delete/" + lang_code + "_mono.txt", "w") as fout:
                print(all_mono_ocred, file=fout)
        else:
            if os.path.isfile(path_output + "/delete/" + lang_code + "_mono.txt") and sum(
                    1 for _ in open(path_output + "/delete/" + lang_code + "_mono.txt")) == data_size:
                print(path_output + "/delete/" + lang_code + "_mono.txt exists and has " + str(data_size) + " lines")
            else:
                all_mono_ocred = add_deletion_errors(all_error_types, all_mono, error_rate)
                with open(path_output + "/delete/" + lang_code + "_mono.txt", "w") as fout:
                    print(all_mono_ocred, file=fout)
                write_error_rate(all_mono_ocred, all_mono, path_output, lang_code, size)

    # add insertion errors in all_mono data and write the error rate results in file
    all_mono = " ".join(mono)
    if os.path.isfile(path_output + "/insert/" + lang_code + "_mono.txt") and sum(
            1 for _ in open(path_output + "/insert/" + lang_code + "_mono.txt")) == data_size:
        print(path_output + "/insert/" + lang_code + "_mono.txt exists and has " + str(data_size) + " lines")
    else:
        all_mono_ocred = add_insertion_errors(all_error_types, all_mono, error_rate)
        with open(path_output + "/insert/" + lang_code + "_mono.txt", "w") as fout:
            print(all_mono_ocred, file=fout)
        write_error_rate(all_mono_ocred, all_mono, path_output, lang_code, size)


def get_real_error_rate(data_type, size):
    with open("Data/backtranslation/data_cer_" + size + "/error_rates.txt", encoding="utf8") as f:
        error_rates = f.readlines()

    data_type = "/" + "/".join(data_type.split()) + "_mono"
    for line in error_rates:
        if data_type in line:
            _, cer, wer = line.split()
    return cer, wer


def read_finetuning_results(max_error_rate, output_file, size):
    if 'flores' in output_file:
        dict_finetune_clean_results = {'amh': 2.5, 'nep': 0.1, 'lao': 6.7, 'khm': 9.8, 'pus': 10.0, 'jpn': 22.8,
                                       'tam': 3.4}
    else:  # finetuned ocred data
        dict_finetune_clean_results = {'amh': 3.4, 'nep': 0.4, 'lao': 8.6, 'khm': 10.0, 'pus': 9.9, 'jpn': 22.9,
                                       'tam': 3.1}
    csv_out = {'gt_score': [], 'ocr_score': [], 'delta_spBLEU': [], 'CER': [], 'Language': [], 'Error type': []}
    dict_lang_error_type = {}

    with open("Data/backtranslation/data_cer_" + size + "/results3.txt", encoding="utf8") as f:
        results = f.readlines()

    # add finetune on clean results
    unique_combinations = list(product(['khm', 'pus', 'lao', 'tam'], ['insert', 'delete', 'replace'])) + [
        ('jpn', 'insert')]
    for [lang, error_type] in unique_combinations:
        csv_out['gt_score'].append(dict_finetune_clean_results[lang])
        csv_out['ocr_score'].append(dict_finetune_clean_results[lang])
        csv_out['delta_spBLEU'].append(0)
        csv_out['CER'].append(0)
        csv_out['Language'].append(lang)
        csv_out['Error type'].append(error_type)
        dict_lang_error_type[(lang, error_type)] = [(0.0, 0)]

    for i, data in enumerate(results):
        duplicate = False
        if i % 2 == 0:
            data_type = data.strip()
            lang = data_type.split()[1]
            cer, _ = get_real_error_rate(data_type, size)
            _, error_type = data_type.split()[0].split("/")
            error_rate = round(float(cer), 2)
            error_rate = int(error_rate) if ((int(error_rate) % 2) == 0) else int(
                error_rate) + 1  # round to the nearest even
        else:
            score = float(data.split("=")[1].split()[0])
            delta_spBLEU = score - dict_finetune_clean_results[lang]
            if error_rate > max_error_rate:  # limit to max_error_rate error rate
                continue
            for j in range(len(csv_out['Language'])):
                if (((csv_out['Language'][j] == lang) and (csv_out['Error type'][j] == error_type)) and (
                        csv_out['CER'][j] == error_rate)):
                    duplicate = True
                    break
            if not duplicate:
                csv_out['gt_score'].append(dict_finetune_clean_results[lang])
                csv_out['ocr_score'].append(score)
                csv_out['delta_spBLEU'].append(delta_spBLEU)
                csv_out['CER'].append(error_rate)
                csv_out['Language'].append(lang)
                csv_out['Error type'].append(error_type)

    df = pd.DataFrame.from_dict(csv_out)
    sorted_df = df.sort_values(by=["CER"], ascending=True)  # sort by CER
    pd.DataFrame(sorted_df).reset_index().to_csv('Data/backtranslation/results/BT/' + size + "/" + output_file + '.csv',
                                                 header=True, index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", choices=["10k", "20k"], default="10k")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    for lang_code in ["pus", "khm", "lao", "tam", "jpn"]:
        read_monolingual_data(lang_code, size=args.size)

        prep_data_for_backtranslation()
        all_error_types = extract_OCR_errors("Data/UDHR/UDHR_" + lang_code + "_GT.txt",
                                             "Data/UDHR/UDHR_" + lang_code + "_OCR.txt")
        for error_rate in range(1, 22, 2):
            introduce_errors_in_monolingual(all_error_types, lang_code, error_rate, size=args.size)

            for operation in ['delete', 'insert', 'replace']:
                print(error_rate, operation)
                input_path = "Data/backtranslation/data_cer/" + str(
                    error_rate) + "/" + operation + "/" + lang_code + "_mono.txt"
                output_path = "Data/MONOLINGUAL/" + args.size + "/" + lang_code + "_mono.txt"
                measure_ocr_error_rate(input_path, output_path)


if __name__ == "__main__":
    main()
