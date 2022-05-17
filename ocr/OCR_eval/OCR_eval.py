#!/usr/bin/env python
import argparse
import glob
import os
from os import path
from typing import Mapping, Any, Tuple, Sequence

import numpy as np
import pandas as pd
from tqdm.auto import tqdm

from data_collection.augment_data import run_augmentation
from data_collection.utils import create_dictionary_lang, return_all_anomalies, sentence_split
from metrics import compute_metrics


def read_ocr_codes_file() -> Tuple[Sequence[str], Sequence[str]]:
    df = pd.read_csv('Data/language_codes/languages_fonts_codes.csv')
    lang_codes = df["Code"].tolist()
    lang_tesseract_codes = df["Tesseract Code"].replace(np.nan, '').tolist()
    return lang_codes, lang_tesseract_codes


def run_on_Flores(lang_code: str, lang_name: str, ocr_system: str):
    root_lang_name = os.path.join("Data", "FLORES", lang_name)
    os.makedirs(os.path.join(root_lang_name, ocr_system), exist_ok=True)

    dict_results = {lang_name: ['', '']}
    groundtruth_split_input = root_lang_name + "txt/" + lang_code + "_split.txt"
    predicted_split_output = root_lang_name + ocr_system + "/" + lang_code + "_sentsplit.txt"

    print(lang_name + ": " + lang_code)
    print("pred: " + predicted_split_output + "; gt: " + groundtruth_split_input)

    if not os.path.isfile(predicted_split_output):
        print("No path: " + predicted_split_output)
        return
    if ocr_system != "googlevision" and os.path.isfile(predicted_split_output):
        print("Removing existing file: " + predicted_split_output)
        os.remove(predicted_split_output)

    if ocr_system == "tesseract":
        print("Running Tesseract")
        lang_codes, lang_Tesseract_codes = read_ocr_codes_file()
        Tesseract_code = lang_Tesseract_codes[lang_codes.index(lang_code)]
        print(Tesseract_code)
        if not Tesseract_code:
            print("No Tesseract training data for " + lang_name)
        else:
            path_img = root_lang_name + "png/" + lang_code + "/"
            all_img_files = sorted([f for f in glob.glob(path_img + "*.png")])

            for name_img in all_img_files:
                name_img = name_img.split("/")[-1][:-4]
                image_input = path_img + name_img + ".png"
                tesseract_output = root_lang_name + "tesseract/" + name_img + "_tesseract"
                os.system(
                    "tesseract " + str(image_input) + " " + str(tesseract_output) + " -l " + Tesseract_code
                )
                sentence_split(input_=tesseract_output, output=predicted_split_output, mode='a')

    elif ocr_system == "googlevision":
        print("Running " + ocr_system + ": results already on")
    else:
        raise ValueError("Wrong ocr_system name: " + ocr_system)

    CER, WER = compute_metrics(
        pred=predicted_split_output, tgt=groundtruth_split_input
    )
    print("{:.2f}".format(CER) + "," + "{:.2f}".format(WER))
    print(" -------------------- ")
    dict_results[lang_name] = ["{:.2f}".format(CER), "{:.2f}".format(WER)]
    return dict_results


def average_error_rates(lang_name, list_error_rates, dict_results):
    CERs = [CER for [_, CER, _] in list_error_rates]
    WERs = [WER for [_, _, WER] in list_error_rates]
    mean_CER = np.mean(np.array(CERs), axis=0)
    mean_WER = np.mean(np.array(WERs), axis=0)
    dict_results[lang_name] = ["{:.2f}".format(mean_CER), "{:.2f}".format(mean_WER)]
    print("mean CER: " + str(mean_CER) + "; mean WER: " + str(mean_WER))
    return dict_results


def run_on_udhr(lang_code: str, lang_name: str, ocr_system: str, dict_all_anomalies):
    root_lang_name = os.path.join("Data/UDHR", lang_name)
    os.makedirs(root_lang_name, exist_ok=True)
    os.makedirs(os.path.join(root_lang_name, ocr_system), exist_ok=True)
    dict_results = {lang_name: ['', '']}

    lang_codes, lang_Tesseract_codes = read_ocr_codes_file()
    Tesseract_code = lang_Tesseract_codes[lang_codes.index(lang_code)]
    if lang_code == 'ckb':
        Tesseract_code = 'tur'  # FLORES has arabic script for Sorani-Kurdish
    print(Tesseract_code)

    list_anomaly_articles = dict_all_anomalies[lang_code]

    if not Tesseract_code:
        print("No Tesseract training data for " + lang_name)
    else:
        list_error_rates = []
        for i in range(1, 31):
            if i in list_anomaly_articles:
                print("not processing anomaly: article " + str(i))
                continue
            print("Article " + str(i))
            name_img = lang_code + str(i)
            path_image_input = os.path.join("Data", "UDHR", "annotations", lang_code)
            if glob.glob(os.path.join(path_image_input, "*.png")):  # input can be png or jpg
                image_input = os.path.join(path_image_input, f"{lang_code}_{i}.png")
            elif glob.glob(os.path.join(path_image_input, "*.PNG")):  # input can be png or jpg
                image_input = os.path.join(path_image_input, f"{lang_code}_{i}.PNG")
            elif glob.glob(os.path.join(path_image_input, "*.jpg")):
                image_input = os.path.join(path_image_input, f"{lang_code}_{i}.jpg")
            elif glob.glob(os.path.join(path_image_input, "*.JPG")):
                image_input = os.path.join(path_image_input, f"{lang_code}_{i}.JPG")
            else:
                print("Extension different than png or jpg or img not there")
                break
            if not path.exists(image_input):
                print(image_input + " doesn't exist")
                continue

            groundtruth_input = os.path.join(root_lang_name, name_img + ".txt")
            groundtruth_split_input = os.path.join(root_lang_name, name_img + "_split.txt")
            predicted_split_output = os.path.join(root_lang_name, ocr_system, name_img + "_sentsplit.txt")
            print("pred: " + predicted_split_output + "; gt: " + groundtruth_split_input)

            # save GT text split into sentences
            with open(groundtruth_input, encoding="utf8") as file:
                input_txt = file.read().split("\n")
            with open(groundtruth_split_input, 'w', encoding="utf-8") as file:
                file.write(" ".join(input_txt))

            if ocr_system == "tesseract":
                tesseract_output = os.path.join(root_lang_name, "tesseract", name_img + "_tesseract")
                if not os.path.isfile(predicted_split_output):
                    os.system(
                        "tesseract " + str(image_input) + " " + str(tesseract_output) + " -l " + Tesseract_code
                    )

                    sentence_split(input_=tesseract_output, output=predicted_split_output, mode='w')

            CER, WER = compute_metrics(predicted_split_output, groundtruth_split_input)
            list_error_rates.append([i, CER, WER])
            print("{:.2f}".format(CER), "{:.2f}".format(WER))
            print(" -------------------- ")
        dict_results = average_error_rates(lang_name, list_error_rates, dict_results)
    return dict_results


def run_ocr_eval(dataset: str, lang_code: str, lang_name: str, ocr_system: str,
                 dict_all_anomalies) -> Mapping[str, Any]:
    if dataset == "FLORES":
        return run_on_Flores(lang_code, lang_name, ocr_system)
    elif dataset == "UDHR":
        return run_on_udhr(lang_code, lang_name, ocr_system, dict_all_anomalies)
    else:
        raise ValueError(f"Unknown dataset: {dataset}")


def run_tess_on_books(lang_code: str = "nep") -> None:
    root_lang_name = os.path.join("Data", "crawls", lang_code)
    path_img = os.path.join(root_lang_name, "png")
    all_img_files = sorted([f for f in glob.iglob(path_img + "*.png")])

    for path_img_in in all_img_files:
        path_tiff_out = os.path.join(root_lang_name, "tiff",
                                     os.path.splitext(os.path.basename(path_img_in))[0] + ".tiff")
        os.system("convert -density 300 " + path_img_in + " -quality 100 " + path_tiff_out)

    predicted_split_output = os.path.join(root_lang_name, lang_code + "_tess_sentsplit.txt")
    filenames = []
    for name_img in all_img_files:
        name_img = os.path.splitext(os.path.basename(name_img))[0]
        tesseract_output = os.path.join(root_lang_name, "tesseract", name_img + "_tesseract")
        filenames.append(tesseract_output + ".txt")
        if tesseract_output + ".txt" not in glob.glob(os.path.join(root_lang_name, "tesseract", "*.txt")):
            image_input = os.path.join(path_img, name_img + ".png")
            os.system(
                "tesseract " + str(image_input) + " " + str(tesseract_output) + " -l " + lang_code
            )

    count_lines = 0
    with open(predicted_split_output, 'w', encoding="utf-8") as outfile:
        for filename in filenames:
            with open(filename, encoding="utf-8") as infile:
                for line in infile:
                    if line.strip() and len(line.split()) > 5:
                        outfile.write(line)
                        count_lines += 1

    print(count_lines)
    os.system(
        "head -10000 Data/crawls/" + lang_code + "/" + lang_code + "_tess_sentsplit.txt > Data/crawls/" + lang_code
        + "_tess_10k.txt")
    os.system(
        "head -20000 Data/crawls/" + lang_code + "/" + lang_code + "_tess_sentsplit.txt > Data/crawls/" + lang_code
        + "_tess_20k.txt")
    os.system(
        "head -30000 Data/crawls/" + lang_code + "/" + lang_code + "_tess_sentsplit.txt > Data/crawls/" + lang_code
        + "_tess_30k.txt")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["FLORES", "UDHR"], default="UDHR")
    parser.add_argument("--ocr-system", choices=["tesseract", "googlevision"], default="tesseract")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    lang_code_dict = create_dictionary_lang()
    dict_results = {}
    os.makedirs(os.path.join('Data', 'Results', args.ocr_system), exist_ok=True)

    run_tess_on_books()
    for lang_code, lang_name in tqdm(lang_code_dict.items(), total=len(lang_code_dict)):
        dict_results[lang_name] = []
        if args.dataset == "FLORES":
            run_augmentation(lang_code)

        print("----------------")
        print(lang_name, lang_code)

        dict_results = run_ocr_eval(args.dataset, lang_code, lang_name, args.ocr_system, return_all_anomalies())

        pd.DataFrame(dict_results).T.reset_index().to_csv(
            'Data/Results/' + args.ocr_system + '/' + args.dataset + '.csv', mode='a',
            header=False, index=False)


if __name__ == "__main__":
    main()
