#!/usr/bin/env python
import glob
import json
import os

import cv2
import numpy as np
import requests
import xmltodict
from PIL import Image
from pdf2image import convert_from_path

from utils import udhr_lang_code, lang_code_xml

print("There are", len(set(udhr_lang_code)), "different languages")

output_folder_pdf = "Data/UDHR/pdfs"
output_folder_img = "Data/UDHR/imgs"
output_folder_txt = "Data/UDHR/txt"


def save_txt(lang_code: str, lang_code_xml) -> None:
    lang_code_xml = lang_code_xml.get(lang_code, lang_code)

    print("Getting xml UDHR file", lang_code_xml + ".xml")
    url = "https://www.unicode.org/udhr/d/udhr_" + lang_code_xml + ".xml"
    response = requests.get(url, allow_redirects=True)

    print("Parsing xml UDHR file", lang_code_xml + ".xml")
    dict = xmltodict.parse(response.content)
    all_articles = dict["udhr"]["article"]
    print("There are", len(all_articles), "articles.")
    dict_paragraphs = {}
    for i in range(len(all_articles)):
        article_nb = i + 1
        dict_paragraphs[article_nb] = []
        title = all_articles[i]['title']
        if 'para' in all_articles[i]:
            if type(all_articles[i]['para']) is list:  # format is inconsistent
                for paragraph in all_articles[i]['para']:
                    if paragraph is not None:  # format issues
                        if not dict_paragraphs[article_nb]:
                            dict_paragraphs[article_nb].append(title + " " + paragraph)
                        else:
                            dict_paragraphs[article_nb].append(paragraph)
            else:
                if not dict_paragraphs[article_nb]:
                    dict_paragraphs[article_nb].append(title + " " + all_articles[i]['para'])
                else:
                    dict_paragraphs[article_nb].append(all_articles[i]['para'])
        else:
            for paragraph in all_articles[i]['orderedlist']['listitem']:
                if paragraph is not None:  # format issues
                    if not dict_paragraphs[article_nb]:
                        if '@tag' in paragraph:
                            dict_paragraphs[article_nb].append(
                                title + " " + paragraph['@tag'] + " " + paragraph['para'])
                        else:
                            dict_paragraphs[article_nb].append(title + " " + paragraph['para'])
                    else:
                        if '@tag' in paragraph:
                            dict_paragraphs[article_nb].append(paragraph['@tag'] + " " + paragraph['para'])
                        else:
                            dict_paragraphs[article_nb].append(paragraph['para'])

    if len(dict_paragraphs) != 30:
        raise ValueError("NOT 30 XML articles!!!")

    print("Saving text data json UDHR file", lang_code + ".json")
    output_file = output_folder_txt + lang_code + ".json"
    os.makedirs(output_folder_txt, exist_ok=True)
    with open(output_file, 'w+', encoding='utf-8') as file:
        json.dump(dict_paragraphs, file, ensure_ascii=False)


def save_pdfs(lang_code: str) -> None:
    print("Saving pdf UDHR file", lang_code + ".pdf")
    url = "https://www.ohchr.org/EN/UDHR/Documents/UDHR_Translations/" + udhr_lang_code[lang_code] + ".pdf"
    response = requests.get(url, allow_redirects=True)
    os.makedirs(output_folder_pdf, exist_ok=True)
    with open(os.path.join(output_folder_pdf, lang_code + ".pdf"), 'wb') as file:
        file.write(response.content)


def convert_pdf_to_png(lang_code: str) -> None:
    path_pdf_in = os.path.join(output_folder_pdf, lang_code + ".pdf")
    folder_jpg_out = os.path.join(output_folder_img, lang_code, "jpgs")
    path_jpg_out = os.path.join(folder_jpg_out, lang_code)
    os.makedirs(folder_jpg_out, exist_ok=True)
    if lang_code in ['arb', 'ukr']:
        for i, image in enumerate(convert_from_path(path_pdf_in)):
            image.save(f'{path_jpg_out}-{i}.jpg', 'JPEG')  # Save pages as images in the PDF file.
    else:
        os.system(f"convert -density 300 {path_pdf_in} -quality 100 {path_jpg_out}.jpg")


def join_imgs(lang_code: str) -> None:
    list_im = glob.glob(os.path.join(output_folder_img, lang_code, "jpgs") + "/*.jpg")
    images = [Image.open(i).convert('L') for i in sorted(list_im)]
    # pick the image which is the smallest, and resize the others to match it (can be arbitrary image shape here)
    min_shape = sorted([(np.sum(image.size), image.size) for image in images])[0][1]
    # for a vertical stacking it is simple: use vstack
    imgs_comb = np.vstack([np.asarray(i.resize(min_shape)) for i in images])
    imgs_comb = Image.fromarray(imgs_comb)
    imgs_comb.save(output_folder_img + "/" + lang_code + "/" + lang_code + '.png')


def split_by_coordinates(lang_code: str) -> None:
    with open('Data/language_codes/article_coordinates.json', encoding="utf-8") as file:
        coordinates = json.load(file)

    path_out = os.path.join(output_folder_img, lang_code, "articles")
    os.makedirs(path_out, exist_ok=True)

    image = cv2.imread(os.path.join(output_folder_img, lang_code, lang_code + '.png'))
    for key in coordinates:
        lang_code1 = key.split("_")[0]
        if lang_code != lang_code1:
            continue
        name_article = key
        (startX, startY), (endX, endY) = coordinates[key]

        cropped_image = image[startY:endY, startX:endX]
        cv2.imwrite(path_out + name_article + '.jpg', cropped_image)


def convert_udhr_a_b(lang_code: str) -> None:
    files_a_b = glob.glob(output_folder_img + lang_code + "/articles/*a.jpg")
    for file_a_b in files_a_b:
        name = file_a_b.split("/")[-1][:-5]
        path_file = "/".join(file_a_b.split("/")[:-1])
        file_name = path_file + "/" + name
        os.system('convert -append ' + file_name + '{a,b}.jpg' + " " + file_name + '.jpg')


def split_pdf_into_articles(lang_code: str) -> None:
    convert_pdf_to_png(lang_code)
    join_imgs(lang_code)
    split_by_coordinates(lang_code)
    convert_udhr_a_b(lang_code)  # Concatenate the split articles.


def main() -> None:
    for lang_code in udhr_lang_code:
        if lang_code == 'isl':
            continue
        print("-------------", lang_code, "----------------")
        save_pdfs(lang_code)
        save_txt(lang_code, lang_code_xml)
        split_pdf_into_articles(lang_code)


if __name__ == "__main__":
    main()
