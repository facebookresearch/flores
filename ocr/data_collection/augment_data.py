#!/usr/bin/env python3
import os
import cv2
import numpy as np
from skimage import io
from skimage import transform as tf
from utils import create_dictionary_lang
import pandas as pd
import glob
import re

lang_code_dict = create_dictionary_lang()
root_dir = "Data/FLORES/"


# TODO: font weight?
dict_properties = {
    "color": ["black"],
    "opacity": ["1", "0.3"],
    "font_size": ["20px"],
    "letter_spacing": ["normal", "0.2em", "-0.2em"],
    "italic": [True, False],
    "bold": [True, False],
    "gauss": [True, False],
    "skew": [True, False]
}

def read_fonts_file():
    df = pd.read_csv('Data/misc/languages_fonts_codes.csv')
    lang_codes = df["Code"].tolist()
    lang_fonts = df["Fonts"].tolist()
    return lang_codes, lang_fonts

def create_style_file(
    font, color, opacity, font_size, letter_spacing, italic, bold, name_style
):
    str_font = "src: url(fonts/" + font + ".ttf);"
    full_style = (
        """
    @font-face {
    font-family: defined_font;
    """
        + str_font
        + """
    }
    p {
        font-family: defined_font;
        color: """
        + color
        + ";"
        + """
        opacity: """
        + opacity
        + ";"
        + """
        letter-spacing:"""
        + letter_spacing
        + ";"
        + """
        font-size:"""
        + font_size
        + ";"
    )
    if italic:
        full_style += """
        font-style: italic;"""
    if bold:
        full_style += """
        font-weight: bold;"""

    full_style += """
    }
    """
    with open("Data/augmentation/styles/" + name_style + ".css", "w+") as f:
        f.write(full_style)


def create_html_file(root_path, list_sentences, name_html_file, name_style):
    str_style = (
        """<link rel="stylesheet" href="/Users/oignat/Desktop/flores_OCR/Data/augmentation/styles/"""
        + name_style
        + """.css">"""
    )
    str_html_head = (
        """
    <!DOCTYPE html>
    <html lang="en">

    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content=
          "width=device-width, initial-scale=1.0">
    """
        + str_style
        + """
    </head>
    <body>
    """
    )
    # put all text into one paragraph
    str_html_text = "<p>"
    for sentences in list_sentences:
        str_html_text += sentences
    str_html_text += "</p>"

    str_html_head_close = """
    </body>
    </html>
    """
    full_text = str_html_head + str_html_text + str_html_head_close
    with open(root_path + name_html_file + ".html", "w+") as f:
        f.write(full_text)


def save_html_to_pdf(root_save_pdfs, root_html_url, name_html_file, lang_name):
    os.system(
        "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --headless --print-to-pdf-no-header --print-to-pdf="
        + root_save_pdfs
        + name_html_file
        + ".pdf "
        + root_html_url
        + name_html_file
        + ".html"
    )
    # os.makedirs("Data/FLORES/" + lang_name + "/pdf/", exist_ok=True)
    # os.system("cp " + root_save_pdfs + name_html_file + ".pdf " + "Data/FLORES/" + lang_name + "/pdf/" + name_html_file + ".pdf")


def save_pdf_to_png(lang_name, name_file, name_html_file):
    # if entire pdf -> need to first split into pages
    root_path = "Data/FLORES/"
    root_save_pdfs = "Data/augmentation/pdfs/"
    os.makedirs(root_path + lang_name + "/png/" + name_file, exist_ok=True)
    path_png_out = root_path + lang_name + "/png/" + name_file + "/" + name_html_file
    path_pdf_in = root_save_pdfs + name_html_file + ".pdf"
    print("Saving pdf to png for " + lang_name)
    os.system("convert -density 300 -trim " + path_pdf_in + " -quality 100 " + path_png_out + "%02d.png")


def add_gaussian_noise(lang_name, name_file, name_html_file):
    root_path = "Data/FLORES/"
    img = cv2.imread(
        root_path + lang_name + "/png/" + name_file + "/" + name_html_file + ".png"
    )
    # Generate Gaussian noise
    gauss = np.random.normal(0, 1, img.size)
    gauss = gauss.reshape(img.shape[0], img.shape[1], img.shape[2]).astype("uint8")
    # Add the Gaussian noise to the image
    img_gauss = cv2.add(img, gauss)

    img_gauss = cv2.cvtColor(img_gauss, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(
        root_path
        + lang_name
        + "/png/"
        + name_file
        + "/"
        + name_html_file
        + "_gauss"
        + ".png",
        img_gauss,
    )

def add_salt_pepper_noise(lang_name, name_file, name_html_file, amount, s_vs_p):
    root_path = "Data/FLORES/"
    image = cv2.imread(
        root_path + lang_name + "/png/" + name_file + "/" + name_html_file + ".png"
    )
    row,col,ch = image.shape
    img_noise = np.copy(image)
    # Salt mode
    num_salt = np.ceil(amount * image.size * s_vs_p)
    coords = [np.random.randint(0, i - 1, int(num_salt)) for i in image.shape]
    img_noise[coords] = 1

    # Pepper mode
    num_pepper = np.ceil(amount* image.size * (1. - s_vs_p))
    coords = [np.random.randint(0, i - 1, int(num_pepper)) for i in image.shape]
    img_noise[coords] = 0
    img_noise = cv2.cvtColor(img_noise, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(
        root_path
        + lang_name
        + "/png/"
        + name_file
        + "/"
        + name_html_file
        + "_salt_pepper"
        + ".png",
        img_noise,
    )

def add_speckle_noise(lang_name, name_file, name_html_file):
    root_path = "Data/FLORES/"
    img = cv2.imread(
        root_path + lang_name + "/png/" + name_file + "/" + name_html_file + ".png"
    )
    gauss = np.random.normal(0, 1, img.size)
    gauss = gauss.reshape(img.shape[0], img.shape[1], img.shape[2]).astype('uint8')
    img_noise = img + img * gauss
    img_noise = cv2.cvtColor(img_noise, cv2.COLOR_BGR2GRAY)

    cv2.imwrite(
        root_path
        + lang_name
        + "/png/"
        + name_file
        + "/"
        + name_html_file
        + "_gauss"
        + ".png",
        img_noise,
    )


def add_skew(lang_name, name_file, name_html_file):
    root_path = "Data/FLORES/"
    img = cv2.imread(
        root_path + lang_name + "/png/" + name_file + "/" + name_html_file + ".png"
    )
    # Create Afine transform
    afine_tf = tf.AffineTransform(shear=0.1)
    # Apply transform to image data
    img_skew = tf.warp(img, inverse_map=afine_tf) * 255
    cv2.imwrite(
        root_path
        + lang_name
        + "/png/"
        + name_file
        + "/"
        + name_html_file
        + "_skew"
        + ".png",
        img_skew,
    )

def run_augmentation_UDHR(lang_code):
    lang_name = lang_code_dict[lang_code]
    root_lang_name = root_dir + lang_name + "/"

    lang_codes, lang_fonts = read_fonts_file()
    index_lang_code = lang_codes.index(lang_code)

    fonts = lang_fonts[index_lang_code].split("; ")

    font_size = dict_properties["font_size"][0]
    color = dict_properties["color"][0]
    opacity = dict_properties["opacity"][0]
    letter_spacing = dict_properties["letter_spacing"][0]
    italic = dict_properties["italic"][1]
    bold = dict_properties["bold"][1]
    gauss = dict_properties["gauss"][1]
    skew = dict_properties["skew"][1]

    font = fonts[0]
    root = 'Data/UDHR/' + lang_name + "/"
    root_path = 'Data/UDHR/annotations/' + lang_code + "/pdfs_synth/"
    os.makedirs(root_path, exist_ok=True)
    txt_files = glob.glob(root + '/*[0-9].txt')
    name_style = (
        font + "_" + color.replace("#", "") + "_" + opacity + "_" + letter_spacing
    )
    if italic:
        name_style += "_" + "italic"
    if bold:
        name_style += "_" + "bold"

    for txt_file in txt_files:
        with open(txt_file, "r", encoding="utf8") as f:
            list_sentences = f.read()
        name_file = txt_file.split("/")[-1][:-4]
        nb = str(re.findall(r'\d+', name_file)[0])
        name_html_file = lang_code + "_" + nb
        create_html_file(root_path, list_sentences, name_html_file, name_style)

        root_save_pdfs = root_path
        root_html_url = root_path
        save_html_to_pdf(root_save_pdfs, root_html_url, name_html_file, lang_name)
        print("Saving pdf to png for " + name_html_file)
        path_png_out = root_path + name_html_file + ".png"
        path_pdf_in = root_path + name_html_file + ".pdf"
        os.system("convert -density 300 -trim " + path_pdf_in + " -quality 100 " + path_png_out)



def run_augmentation(lang_code):
    lang_name = lang_code_dict[lang_code]
    root_lang_name = root_dir + lang_name + "/"

    lang_codes, lang_fonts = read_fonts_file()
    index_lang_code = lang_codes.index(lang_code)

    fonts = lang_fonts[index_lang_code].split("; ")

    font_size = dict_properties["font_size"][0]
    color = dict_properties["color"][0]
    opacity = dict_properties["opacity"][0]
    letter_spacing = dict_properties["letter_spacing"][0]
    italic = dict_properties["italic"][1]
    bold = dict_properties["bold"][1]
    gauss = dict_properties["gauss"][1]
    skew = dict_properties["skew"][1]

    # for font in fonts:
    # for i in range(1, 5):
        # name_file = lang_code + str(i)
    font = fonts[0]
    name_file = lang_code
    with open(root_lang_name + "/" + name_file + ".txt", "r+") as f:
        list_sentences = f.readlines()

    name_style = (
        font + "_" + color.replace("#", "") + "_" + opacity + "_" + letter_spacing
    )
    if italic:
        name_style += "_" + "italic"
    if bold:
        name_style += "_" + "bold"
    name_html_file = name_file + "_" + name_style

    # create_style_file(font, color, opacity, font_size, letter_spacing, italic, bold, name_style)
    root_path = "Data/augmentation/htmls/"
    create_html_file(root_path, list_sentences, name_html_file, name_style)

    root_save_pdfs = "/Users/oignat/Desktop/flores_OCR/Data/augmentation/pdfs/"
    root_html_url = "file:///Users/oignat/Desktop/flores_OCR/Data/augmentation/htmls/"
    save_html_to_pdf(root_save_pdfs, root_html_url, name_html_file, lang_name)
    save_pdf_to_png(lang_name, name_file, name_html_file)
    if gauss:
        # add_speckle_noise(lang_name, name_file, name_html_file) #too much
        # add_gaussian_noise(lang_name, name_file, name_html_file) #too little ~
        add_salt_pepper_noise(lang_name, name_file, name_html_file, amount=0.005, s_vs_p=0.5)
    if skew:
        add_skew(lang_name, name_file, name_html_file)


if __name__ == "__main__":
    for lang_code in lang_code_dict.keys():
        run_augmentation(lang_code)
        # run_augmentation_UDHR(lang_code) #just for UDHR synthetic PDF data
