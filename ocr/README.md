# OCR Improves Machine Translation for Low-Resource Languages

This folder contains the scripts to run the data preparation and evaluation for the following paper.

```
@inproceedings{ignat2022ocr,
  author = "Oana Ignat and Jean Maillard and Vishrav Chaudhary and Francisco Guzmán",
  title = "OCR Improves Machine Translation for Low-Resource Languages",
  booktitle = "Findings of ACL 2022, Long Papers",
  year = 2022
}
```

Contents:
* Design and build a benchmark in 60 languages that includes a variety of languages, scripts (UDHR data and Flores 101)
    * Code to download and process UDHR articles: [`data_collection/download_UDHR_data.py`](data_collection/download_UDHR_data.py)
    * Code to Augment Flores 101 PDFs (font, opacity, letter-spacing, italic, bold, Gaussian noise, skewing): [`data_collection/augment_data.py`](data_collection/augment_data.py)

* Evaluate related work under this new benchmark
    * Code to run Google Vision API: [`OCR_eval/google_vision_OCR.py`](OCR_eval/google_vision_OCR.py)
     * Code to run Tesseract and measure metrics: [`OCR_eval/OCR_eval.py`](OCR_eval/OCR_eval.py)

* Study the downstream impact of recognition errors in back translation
    * Code to extract OCR errors from UDHR and insert them in monolingual data (WikiMatrix and CC100): [`OCR_impact_BT/OCR_error_analysis.py`](OCR_impact_BT/OCR_error_analysis.py)
    * Code run BT and finetune MM124 model on OCRed monolingual data: [`OCR_impact_BT/translate_mono.sh`](OCR_impact_BT/translate_mono.sh), [`OCR_impact_BT/finetune.sh`](OCR_impact_BT/finetune.sh) , [`OCR_impact_BT/evaluate.sh`](OCR_impact_BT/evaluate.sh)
    * Code run BT and finetune MM124 model on OCRed Nepali books: [`OCR_impact_BT/translate_mono_books.sh`](OCR_impact_BT/translate_mono_books.sh), [`OCR_impact_BT/finetune_eval_books.sh`](OCR_impact_BT/finetune_eval_books.sh)
