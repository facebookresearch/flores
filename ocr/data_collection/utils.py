import csv
import numpy as np

# pdf codes might be updated in the meantime in the UDHR website
UDHR_lang_code = {"amh":"amh", "hye":"arm", "ast":"aub", "bel":"ruw", "ben":"bng", "bul":"blg", "mya":"bms", "kat":"geo", "ell":"grk",
"guj":"gjr", "heb":"hbr", "hin":"hnd", "jpn":"jpn", "kan":"kjv", "kaz":"kaz", "khm":"khm", "kor":"kkn", "kir":"kdo", "lao":"nol",
"mkd":"mkj", "mal":"mjs", "mar":"mrt", "npi":"nep", "pbu":"pbu", "pan":"pnj1", "rus":"rus", "srp":"src5", "tgk":"pet",
"tam":"tcv", "tel":"tcw", "tha":"thj", "ukr":"ukr", "urd":"urd", "vie":"vie", "tur":"trk", "uzn":"uzb", "wol":"wol", "arb":"arz",
"ceb":"ceb", "cmn":"chn", "fuv":"fuv", "lug":"lap1", "isl": "ice", "lin":"lin", "mri":"mbf", "khk":"khk", "nya":"nyj", "ron":"rum",
"ckb":"kdb1", "zul":"zuu", "sna":"shd", "umb":"mnf", "swh":"swa", "som":"som", "swe":"swd", "pol":"pql", "slk":"slo", "slv":"slv",
"gaz":"gax", "por":"por"}

lang_code_xml = {"ron":"ron_1953", "ell":"ell_monotonic", "npi":"nep", "fuv":"fuv2", "srp":"srp_cyrl", "uzn":"uzn_latn",
"cmn":"cmn_hans", "nya":"nya_chechewa", "por":"por_PT", "gaz":"gax"}


def get_languages():
    languages = []
    lang_code = []
    with open("Data/language_codes/languages.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            languages.append(row[0])
            lang_code.append(row[1])
    languages = languages[1:]
    lang_code = lang_code[1:]
    return languages, lang_code


def create_dictionary_lang():
    languages, lang_codes = get_languages()
    dict_lang = {}
    for lang_code, lang in zip(lang_codes, languages):
        dict_lang[lang_code] = lang
    # print(dict_lang)
    # print(len(dict_lang.keys()))
    return dict_lang


def mergeDict(dict1, dict2):
   ''' Merge dictionaries and keep values of common keys in list'''
   dict3 = {**dict1, **dict2}
   for key, value in dict3.items():
       if key in dict1 and key in dict2:
               dict3[key] = list(set(value + dict1[key]))
   return dict3

# articles that had an CER > mean + 2 * std -> must be anomalies (not matching pdf & text)
def check_annotations_anomaly(lang_name, list_error_rates):
    error_rates = [er for [_, er] in list_error_rates]
    elements = np.array(error_rates)

    mean = np.mean(elements, axis=0)
    std = np.std(elements, axis=0)

    list_anomalies = []
    print("mean: " + str(mean) + " std: " + str(std))
    for [index, error_rate] in list_error_rates:
        if error_rate >= mean + 2 * std:
            print("Articles: " + str(index) + " CER: " + str(error_rate))
            list_anomalies.append(index)
    return list_anomalies

# I already computed them running both Google & Tesseract
def return_all_anomalies():
    dict_anomalies_google = {'amh': [], 'hye': [], 'ast': [15, 17, 20], 'bel': [20], 'ben': [11], 'bul': [17, 20], 'mya': [3, 17], 'kat': [8], 'ell': [15, 17], 'guj': [3, 30], 'heb': [17], 'hin': [9], 'jpn': [17, 20], 'kan': [9], 'kaz': [15, 20], 'khm': [5, 11], 'kor': [], 'kir': [12, 27], 'lao': [3, 6], 'mkd': [12], 'mal': [10, 13], 'mar': [9], 'npi': [24, 28], 'pbu': [26], 'pan': [17], 'rus': [3], 'srp': [15, 17, 20], 'tgk': [17], 'tam': [15, 24], 'tel': [15], 'tha': [], 'ukr': [6], 'urd': [3], 'vie': [24], 'tur': [15, 20], 'uzn': [5], 'wol': [3], 'zul': [15, 17, 20], 'arb': [17], 'ceb': [20], 'cmn': [], 'fuv': [15], 'lug': [14, 21], 'isl': [6, 10], 'lin': [15, 20], 'mri': [4], 'khk': [13, 17], 'nya': [15, 20], 'ron': [1, 20], 'ckb': [2], 'sna': [15, 17], 'umb': [9, 6, 7, 8, 10, 11, 12, 13, 14], 'swh': [15, 17, 20], 'som': [15, 17, 20], 'swe': [11], 'pol': [15, 17, 20], 'slk': [14], 'slv': [17, 30], 'gaz': [15, 20], 'por': [17]}
    dict_anomalies_tesseract = {'amh': [13, 20, 27], 'hye': [], 'ast': [15, 17, 20], 'bel': [17, 20], 'ben': [13], 'bul': [17, 20], 'mya': [], 'kat': [8], 'ell': [15, 17], 'guj': [3, 30], 'heb': [13, 17], 'hin': [6], 'jpn': [2, 30], 'kan': [9], 'kaz': [15, 17], 'khm': [5, 11], 'kor': [24], 'kir': [15, 20], 'lao': [6], 'mkd': [17, 20], 'mal': [10, 21], 'mar': [29], 'npi': [28], 'pbu': [26], 'pan': [7], 'rus': [15, 17, 20], 'srp': [20], 'tgk': [4], 'tam': [3, 15, 24], 'tel': [15], 'tha': [6, 10], 'ukr': [17, 20], 'urd': [3, 6, 9], 'vie': [], 'tur': [15, 17, 20], 'uzn': [5], 'wol': [15, 17, 20], 'zul': [15, 20], 'arb': [17], 'ceb': [17, 20], 'cmn': [22], 'fuv': [], 'lug': [14, 21], 'isl': [10], 'lin': [15, 20], 'mri': [4], 'khk': [15, 20], 'nya': [20], 'ron': [15, 20], 'ckb': [3, 6], 'sna': [17], 'umb': [9], 'swh': [15, 17, 20], 'som': [15], 'swe': [11], 'pol': [15, 17, 20], 'slk': [14], 'slv': [17, 30], 'gaz': [17, 20], 'por': [6, 13, 24]}
    dict_all_anomalies = mergeDict(dict_anomalies_google, dict_anomalies_tesseract)
    return dict_all_anomalies

def sentence_split(input, output, mode):
    with open(input + ".txt", encoding="utf8") as f:
        input_txt_ocr = f.readlines()

    new_ocr_txt = " ".join(input_txt_ocr)
    new_ocr_txt = " ".join(new_ocr_txt.split()) #remove double spaces

    with open(output, mode, encoding="utf-8") as f:
        f.write(new_ocr_txt)