#!/usr/bin/env python3

import glob
import os
from os import path
import pandas as pd
import numpy as np
import tqdm
from metrics import compute_metrics
import sys
sys.path.append('/private/home/oignat/flores_OCR')
from data_collection.utils import create_dictionary_lang, dict_all_anomalies, sentence_split
from data_collection.augment_data import run_augmentation

DATA = "UDHR"
# DATA = "FLORES"

ocr_system = "tesseract"
# ocr_system = "googlevision"

if DATA == "FLORES":
    root_dir = "/Data/FLORES/"
elif DATA == "UDHR":
    root_dir = "/Data/UDHR/"
else:
    print("DATA param wrong")

lang_code_dict = create_dictionary_lang()
dict_results = {}
os.makedirs('Data/Results/' + ocr_system, exist_ok=True)

def read_ocr_codes_file():
    df = pd.read_csv('Data/language_codes/languages_fonts_codes.csv')
    lang_codes = df["Code"].tolist()
    lang_Tesseract_codes = df["Tesseract Code"].replace(np.nan, '').tolist()
    return lang_codes, lang_Tesseract_codes

def run_on_Flores(lang_code, ocr_system):
    lang_name = lang_code_dict[lang_code]
    root_lang_name = root_dir + lang_name + "/"
    os.makedirs(root_lang_name + ocr_system, exist_ok=True)

    dict_results = {lang_name: ['', '']}
    groundtruth_split_input = root_lang_name + "txt/" + lang_code + "_split.txt"
    predicted_split_output = root_lang_name + ocr_system + "/" + lang_code + "_sentsplit.txt"

    print(lang_name + ": " + lang_code)
    print("pred: " + predicted_split_output + "; gt: " + groundtruth_split_input)

    if not os.path.isfile(predicted_split_output):
        print("No path: " + predicted_split_output)
        return
    # if not os.path.isfile(predicted_split_output):
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
                sentence_split(input=tesseract_output, output=predicted_split_output, mode='a')

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

def run_on_UDHR(lang_code, ocr_system, dict_all_anomalies, dict_replacements):
    lang_name = lang_code_dict[lang_code]
    root_lang_name = root_dir + lang_name + "/"
    os.makedirs(root_lang_name, exist_ok=True)
    os.makedirs(root_lang_name + ocr_system, exist_ok=True)
    dict_results = {lang_name: ['', '']}

    lang_codes, lang_Tesseract_codes = read_ocr_codes_file()
    Tesseract_code = lang_Tesseract_codes[lang_codes.index(lang_code)]
    if lang_code == 'ckb' and DATA == "UDHR":
        Tesseract_code = 'tur' # FLORES has arabic script for Sorani-Kurdish
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
            path_image_input = root_dir + "annotations/" + lang_code + "/"
            # path_image_input = root_dir + "annotations/" + lang_code + "/pdfs_synth/"
            if glob.glob(path_image_input + "*.png"):  # input can be png or jpg
                image_input = path_image_input + lang_code + "_" + str(i) + ".png"
            elif glob.glob(path_image_input + "*.PNG"):  # input can be png or jpg
                image_input = path_image_input + lang_code + "_" + str(i) + ".PNG"
            elif glob.glob(path_image_input + "*.jpg"):
                image_input = path_image_input + lang_code + "_" + str(i) + ".jpg"
            elif glob.glob(path_image_input + "*.JPG"):
                image_input = path_image_input + lang_code + "_" + str(i) + ".JPG"
            else:
                print("Extension different than png or jpg or img not there")
                break
            if not path.exists(image_input):
                print(image_input + " doesn't exist")
                continue

            groundtruth_input = root_lang_name + name_img + ".txt"
            groundtruth_split_input = root_lang_name + name_img + "_split.txt"
            predicted_split_output = root_lang_name + ocr_system + "/" + name_img + "_sentsplit.txt"
            print("pred: " + predicted_split_output + "; gt: " + groundtruth_split_input)

            # save GT text split into sentences
            input_txt = open(groundtruth_input, encoding="utf8").read().split("\n")
            new_gt_txt = " ".join(input_txt)
            with open(groundtruth_split_input, 'w+') as f:
                f.write(new_gt_txt)

            if ocr_system == "tesseract":
                tesseract_output = root_lang_name + "tesseract/" + name_img + "_tesseract"
                if not os.path.isfile(predicted_split_output):
                    os.system(
                            "tesseract " + str(image_input) + " " + str(tesseract_output) + " -l " + Tesseract_code
                        )

                    sentence_split(input=tesseract_output, output=predicted_split_output, mode = 'w')

            CER, WER = compute_metrics(predicted_split_output, groundtruth_split_input)
            list_error_rates.append([i, CER, WER])
            # dict_results[lang_name] = ["{:.2f}".format(CER), "{:.2f}".format(WER)]
            print("{:.2f}".format(CER), "{:.2f}".format(WER))
            print(" -------------------- ")
        # dict_results[lang_name] = list_error_rates
        # print(lang_name)
        dict_results = average_error_rates(lang_name, list_error_rates, dict_results)
    return dict_results, dict_replacements


def run_OCR_eval(lang_code, ocr_system, dict_all_anomalies):
    lang_name = lang_code_dict[lang_code]
    print("----------------")
    print(lang_name, lang_code)
    if DATA == "FLORES":
        dict_results = run_on_Flores(lang_code, ocr_system)
    elif DATA == "UDHR":
        dict_results = run_on_UDHR(lang_code, ocr_system, dict_all_anomalies)
    else:
        print("Wrong data!!")
    return dict_results

def run_Tess_on_books():
    lang_code = "nep"
    root_lang_name = "/Data/crawls/" + lang_code + "/"
    path_img = root_lang_name + "png/"
    all_img_files = sorted([f for f in glob.glob(path_img + "*.png")])

    for path_img_in in all_img_files:
        path_tiff_out = root_lang_name + "tiff/" + path_img_in.split("/")[-1][:-4] + ".tiff"
        os.system("convert -density 300 " + path_img_in + " -quality 100 " + path_tiff_out)

    predicted_split_output = root_lang_name  + lang_code + "_tess_sentsplit.txt"
    filenames = []
    for name_img in all_img_files:
        name_img = name_img.split("/")[-1][:-4]
        tesseract_output = root_lang_name + "tesseract/" + name_img + "_tesseract"
        filenames.append(tesseract_output + ".txt")
        if tesseract_output + ".txt" not in glob.glob(root_lang_name + "tesseract/" + "*.txt"):
            image_input = path_img + name_img + ".png"    
            Tesseract_code = lang_code
            os.system(
                "tesseract " + str(image_input) + " " + str(tesseract_output) + " -l " + Tesseract_code
            )
    
    count_lines = 0
    with open(predicted_split_output, 'w') as outfile:
        for fname in filenames:
            with open(fname) as infile:
                for line in infile:
                    if line.strip() and len(line.split()) > 5:
                        outfile.write(line)
                        count_lines += 1

    print(count_lines) #37227 >5 26409
    os.system("head -10000 Data/crawls/" + lang_code + "/" + lang_code + "_tess_sentsplit.txt > Data/crawls/" + lang_code + "_tess_10k.txt")
    os.system("head -20000 Data/crawls/" + lang_code + "/" + lang_code + "_tess_sentsplit.txt > Data/crawls/" + lang_code + "_tess_20k.txt")
    os.system("head -30000 Data/crawls/" + lang_code + "/" + lang_code + "_tess_sentsplit.txt > Data/crawls/" + lang_code + "_tess_30k.txt")

if __name__ == "__main__":
    run_Tess_on_books()
    
    for lang_code in tqdm(list(lang_code_dict.keys())):
        lang_name = lang_code_dict[lang_code]
        dict_results[lang_name] = []
        if DATA == "FLORES":
            # remove all png from before:
            # shutil.rmtree("Data/FLORES/" + lang_code_dict[lang_code] + "/png", ignore_errors=True)
            run_augmentation(lang_code)
        dict_results = run_OCR_eval(lang_code, ocr_system, dict_all_anomalies)
        pd.DataFrame(dict_results).T.reset_index().to_csv('Data/Results/' + ocr_system + '/'+ DATA +'.csv', mode='a', header=False, index=False)
