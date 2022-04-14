import io
import json
import logging
import os
import re

from data_collection.utils import create_dictionary_lang
from google.cloud import storage, vision

## uncomment if want to activate key
# os.system('export GOOGLE_APPLICATION_CREDENTIALS="yourkey.json"')


def async_detect_document(
    gcs_source_uri, gcs_destination_uri, dict_lang, destination_path
):
    """OCR with PDF/TIFF as source files on GCS"""

    # Supported mime_types are: 'application/pdf' and 'image/tiff'
    mime_type = "image/tiff"

    # How many pages should be grouped into each json output file.
    batch_size = 1

    client = vision.ImageAnnotatorClient()

    feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)

    gcs_source = vision.GcsSource(uri=gcs_source_uri)
    input_config = vision.InputConfig(gcs_source=gcs_source, mime_type=mime_type)

    gcs_destination = vision.GcsDestination(uri=gcs_destination_uri)
    output_config = vision.OutputConfig(
        gcs_destination=gcs_destination, batch_size=batch_size
    )

    async_request = vision.AsyncAnnotateFileRequest(
        features=[feature], input_config=input_config, output_config=output_config
    )

    operation = client.async_batch_annotate_files(requests=[async_request])

    print("Waiting for the operation to finish.")
    operation.result(timeout=420)

    # Once the request has completed and the output has been
    # written to GCS, we can list all the output files.
    storage_client = storage.Client()

    match = re.match(r"gs://([^/]+)/(.+)", gcs_destination_uri)
    bucket_name = match.group(1)
    prefix = match.group(2)

    bucket = storage_client.get_bucket(bucket_name)

    # List objects with the given prefix.
    blob_list = list(bucket.list_blobs(prefix=prefix))
    print("Output files:")
    for blob in blob_list:
        print(blob.name)

    # Process the first output file from GCS.
    # Since we specified batch_size=2, the first response contains
    # the first two pages of the input file.
    output = blob_list[0]

    json_string = output.download_as_string()
    response = json.loads(json_string)

    # The actual response for the first page of the input file.
    first_page_response = response["responses"][0]
    annotation = first_page_response["fullTextAnnotation"]

    # Here we print the full text from the first page.
    # The response contains more information:
    # annotation/pages/blocks/paragraphs/words/symbols
    # including confidence scores and bounding boxes
    # print('Full text:\n')

    input_txt_ocr = annotation["text"].split("\n")
    new_ocr_txt = " ".join(input_txt_ocr)
    new_ocr_txt = " ".join(new_ocr_txt.split())  # remove double spaces

    lang_code = gcs_destination_uri.split("/")[-1].split("_")[0]
    lang_name = dict_lang[lang_code]
    # output_path_ocr = destination_path + gcs_destination_uri.split("/")[-1] + "_sentsplit.txt"
    output_path_ocr = (
        destination_path + gcs_destination_uri.split("/")[-1] + "_sentsplit_synth.txt"
    )
    print(output_path_ocr)
    with open(output_path_ocr, "w", encoding="utf-8") as f:
        f.write(new_ocr_txt)


if __name__ == "__main__":
    root_data = "UDHR"
    # root_data = "FLORES"

    dict_lang = create_dictionary_lang()
    # file_names = sorted(os.listdir("Data/" + root_data + "_tiff/"))
    file_names = sorted(os.listdir("Data/" + root_data + "_tiff_synth/"))
    for file_name in file_names:
        # gcs_source_uri = "gs://ocrdata_flores_udhr/" + root_data + "_tiff/" + file_name
        gcs_source_uri = (
            "gs://ocrdata_flores_udhr/" + root_data + "_tiff_synth/" + file_name
        )
        print(gcs_source_uri)
        # gcs_destination_uri = "gs://ocrdata_flores_udhr/Output_" + root_data + "/" + file_name[:-5]
        gcs_destination_uri = (
            "gs://ocrdata_flores_udhr/Output_" + root_data + "_synth/" + file_name[:-5]
        )
        lang_code = gcs_destination_uri.split("/")[-1].split("_")[0]
        lang_name = dict_lang[lang_code]
        destination_path = "Data/" + root_data + "/" + lang_name + "/googlevision/"
        os.makedirs(destination_path, exist_ok=True)
        file_names_done = os.listdir(destination_path)
        file_name = gcs_destination_uri.split("/")[-1]
        new_file_name = "".join(file_name.split("_")[0:2])
        print(file_name + "_sentsplit.txt")
        print(new_file_name + "_sentsplit.txt")
        # if file_name + "_sentsplit.txt" in file_names_done or new_file_name + "_sentsplit.txt" in file_names_done:
        if (
            file_name + "_sentsplit_synth.txt" in file_names_done
            or new_file_name + "_sentsplit_synth.txt" in file_names_done
        ):
            print(
                "Done: "
                + destination_path
                + gcs_destination_uri.split("/")[-1]
                + "_sentsplit_synth.txt"
            )
            continue
        try:
            async_detect_document(
                gcs_source_uri, gcs_destination_uri, dict_lang, destination_path
            )
        except:
            logging.basicConfig(
                filename="Data/google_ocr.log",
                filemode="w+",
                format="%(name)s - %(levelname)s - %(message)s",
            )
            logging.warning("Fail: " + gcs_source_uri)
