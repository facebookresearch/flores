#!/usr/bin/env python3
import requests
import xmltodict
import json
import os
import glob
import numpy as np
import cv2
from PIL import Image
from pdf2image import convert_from_path
from utils import create_dictionary_lang, UDHR_lang_code, lang_code_xml

print("There are " + str(len(list(set(UDHR_lang_code.keys())))) + " different languages")

output_folder_pdf = "Data/UDHR/pdfs/"
output_folder_img = "Data/UDHR/imgs/"
output_folder_txt = "Data/UDHR/txt/"

def save_txt(lang_code, lang_code_xml):
    if lang_code in lang_code_xml.keys():
        lang_code_xml = lang_code_xml[lang_code]
    else:
        lang_code_xml = lang_code
    
    print("Getting xml UDHR file " + lang_code_xml + ".xml")
    url = "https://www.unicode.org/udhr/d/udhr_" + lang_code_xml + ".xml"
    r = requests.get(url, allow_redirects=True)

    print("Parsing xml UDHR file " + lang_code_xml + ".xml")
    dict = xmltodict.parse(r.content)
    all_articles = dict["udhr"]["article"]
    print("There are " + str(len(all_articles)) + " articles.")
    dict_paragraphs = {}
    for i in range(len(all_articles)):
        article_nb = i + 1
        dict_paragraphs[article_nb] = []
        title = all_articles[i]['title']
        if 'para' in all_articles[i]:
            if type(all_articles[i]['para']) is list: # format is incosistent
                for paragraph in all_articles[i]['para']:
                    if paragraph != None: #format issues
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
                if paragraph != None: #format issues
                    if not dict_paragraphs[article_nb]:
                        if '@tag' in paragraph:
                            dict_paragraphs[article_nb].append(title + " " + paragraph['@tag'] + " " + paragraph['para'])
                        else:
                            dict_paragraphs[article_nb].append(title + " " + paragraph['para'])
                    else:
                        if '@tag' in paragraph:
                            dict_paragraphs[article_nb].append(paragraph['@tag'] + " " + paragraph['para'])
                        else:
                            dict_paragraphs[article_nb].append(paragraph['para'])

    if (len(dict_paragraphs)) != 30:
        raise ValueError("NOT 30 XML articles!!!")
    
    print("Saving text data json UDHR file " + lang_code + ".json")
    output_file = output_folder_txt + lang_code + ".json"
    os.makedirs(output_folder_txt, exist_ok=True)
    with open(output_file, 'w+', encoding='utf-8') as fp:
        json.dump(dict_paragraphs, fp, ensure_ascii=False)

    # optional: read and save all txt files from json
    # lang_name = lang_code_dict[lang_code]
    # root_lang_name = output_folder_txt + lang_name
    # os.makedirs(root_lang_name, exist_ok=True)
    # print("Saving txt UDHR per article: " + root_lang_name + "/" + lang_code + ".txt")
    # with open(output_folder_txt + lang_code + ".json") as f:
    #     txt_data = json.load(f)
    # for key in txt_data:
    #     paragraph = txt_data[key]
    #     content = " ".join(txt_data[key])
    #     if lang_code == "amh":  # amh text file has no spaces
    #         content = content.replace("፡፤", " ፡፤ ")
    #         content = content.replace("፡", " ፡ ")
    #         content = content.replace("፤፣", " ፤፣ ")
    #     with open(root_lang_name + "/" + lang_code + key + ".txt", "w+") as f:
    #         f.write(content)

def save_pdfs(lang_code):
    print("Saving pdf UDHR file " + lang_code + ".pdf")
    url = "https://www.ohchr.org/EN/UDHR/Documents/UDHR_Translations/" + UDHR_lang_code[lang_code] + ".pdf"
    r = requests.get(url, allow_redirects=True)
    output_file = output_folder_pdf + lang_code + ".pdf"
    os.makedirs(output_folder_pdf, exist_ok=True)
    open(output_file, 'wb').write(r.content)


def convert_pdf_to_png(lang_code):
    path_pdf_in = output_folder_pdf + lang_code + ".pdf"
    path_jpg_out = output_folder_img + lang_code + "/jpgs/" + lang_code
    os.makedirs(output_folder_img + lang_code + "/jpgs", exist_ok=True)
    if lang_code in ['arb', 'ukr']:
        images = convert_from_path(path_pdf_in)
        for i in range(len(images)):
            # Save pages as images in the pdf
            images[i].save(path_jpg_out + '-'+ str(i) +'.jpg', 'JPEG')
    else:
        os.system("convert -density 300 " + path_pdf_in + " -quality 100 " + path_jpg_out + ".jpg")


def join_imgs(lang_code):
    list_im = glob.glob(output_folder_img + "/" + lang_code + "/jpgs/*.jpg")
    imgs = [ Image.open(i).convert('L') for i in sorted(list_im) ]
    # pick the image which is the smallest, and resize the others to match it (can be arbitrary image shape here)
    min_shape = sorted( [(np.sum(i.size), i.size ) for i in imgs])[0][1]    
    # for a vertical stacking it is simple: use vstack
    imgs_comb = np.vstack( [np.asarray( i.resize(min_shape) ) for i in imgs ] )
    imgs_comb = Image.fromarray( imgs_comb)
    imgs_comb.save(output_folder_img + "/" + lang_code + "/" +  lang_code + '.png')

def split_by_coordinates(lang_code):
    with open('Data/language_codes/article_coordinates.json') as json_file:
        coordinates = json.load(json_file)

    path_out = output_folder_img + lang_code + "/articles/"
    os.makedirs(path_out, exist_ok=True)

    image = cv2.imread(output_folder_img + lang_code + "/" + lang_code + '.png')
    for key in coordinates.keys():
        lang_code1 = key.split("_")[0]
        if lang_code != lang_code1:
            continue
        name_article = key
        [(startX, startY), (endX, endY)] = coordinates[key]

        cropped_image = image[ startY:endY, startX:endX]
        cv2.imwrite(path_out + name_article + '.jpg', cropped_image)

def convert_UDHR_a_b(lang_code):
    files_a_b = glob.glob(output_folder_img + lang_code + "/articles/*a.jpg")
    for file_a_b in files_a_b:
        name = file_a_b.split("/")[-1][:-5]
        path_file = "/".join(file_a_b.split("/")[:-1])
        file_name = path_file + "/" + name
        os.system('convert -append ' + file_name + '{a,b}.jpg' + " " + file_name + '.jpg')


def split_pdf_into_articles(lang_code):
    convert_pdf_to_png(lang_code)
    join_imgs(lang_code)
    split_by_coordinates(lang_code)
    convert_UDHR_a_b(lang_code) #concatenate splitted articles


if __name__ == "__main__":
    lang_code_dict = create_dictionary_lang()

    for lang_code in UDHR_lang_code.keys():
    # for lang_code in ['ron']:
        if lang_code == 'isl':
            continue
        print("------------- " + lang_code + " ----------------")
        save_pdfs(lang_code)
        save_txt(lang_code, lang_code_xml)
        split_pdf_into_articles(lang_code)
    

    
