import argparse
import json
import logging
import os
import re
from typing import Literal

from google.cloud import storage, vision

from data_collection.utils import create_dictionary_lang


def async_detect_document(
        gcs_source_uri, gcs_destination_uri, destination_path,
        mime_type: Literal["image/tiff", "application/pdf"] = "image/tiff", batch_size: int = 1
):
    """OCR with PDF/TIFF as source files on GCS

    batch_size: how many pages should be grouped into each json output file.
    """
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

    input_txt_ocr = annotation["text"].split("\n")
    new_ocr_txt = " ".join(input_txt_ocr)
    new_ocr_txt = " ".join(new_ocr_txt.split())  # remove double spaces

    output_path_ocr = destination_path + gcs_destination_uri.split("/")[-1] + "_sentsplit_synth.txt"
    print(output_path_ocr)
    with open(output_path_ocr, "w", encoding="utf-8") as f:
        f.write(new_ocr_txt)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["FLORES", "UDHR"], default="UDHR")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    dict_lang = create_dictionary_lang()
    file_names = sorted(os.listdir(os.path.join("Data", args.dataset + "_tiff_synth")))
    for file_name in file_names:
        gcs_source_uri = f"gs://ocrdata_flores_udhr/{args.dataset}_tiff_synth/{file_name}"
        print(gcs_source_uri)
        gcs_destination_uri = f"gs://ocrdata_flores_udhr/Output_{args.dataset}_synth/{file_name[:-5]}"
        lang_code = gcs_destination_uri.split("/")[-1].split("_")[0]
        lang_name = dict_lang[lang_code]
        destination_path = "Data/" + args.dataset + "/" + lang_name + "/googlevision/"
        os.makedirs(destination_path, exist_ok=True)
        file_names_done = os.listdir(destination_path)
        file_name = gcs_destination_uri.split("/")[-1]
        new_file_name = "".join(file_name.split("_")[:2])
        print(file_name + "_sentsplit.txt")
        print(new_file_name + "_sentsplit.txt")

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
                gcs_source_uri, gcs_destination_uri, destination_path
            )
        except:
            logging.basicConfig(
                filename="Data/google_ocr.log",
                filemode="w+",
                format="%(name)s - %(levelname)s - %(message)s",
            )
            logging.warning("Fail: " + gcs_source_uri)


if __name__ == "__main__":
    main()
