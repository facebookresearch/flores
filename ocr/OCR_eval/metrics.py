"""Script to compute character error rate and word error rate between a predicted text and its "gold" target text.

Usage:
python metrics.py --pred [predicted_filename] --tgt [target_filename]

Copyright (c) 2021, Shruti Rijhwani
All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of <https://github.com/shrutirij/ocr-post-correction>
"""
import argparse
import unicodedata
from collections import defaultdict

import editdistance as ed


def check_splitted_words(predicted_text):
    new_predicted = []
    pred_spl = predicted_text.split()
    i = 0
    while i < len(pred_spl) - 1:
        if pred_spl[i][-1] == "-":
            new_word = pred_spl[i][:-1] + pred_spl[i + 1]
            new_predicted.append(new_word)
            i = i + 2
        else:
            new_predicted.append(pred_spl[i])
            i = i + 1
    return " ".join(new_predicted)


class ErrorMetrics:
    def preprocess(self, text):
        preprocessed = " ".join(text.strip().split())
        return preprocessed

    def calculate_metrics(self, predicted_text, transcript):
        print("Metrics:")
        predicted_text = predicted_text.replace("\u200d", "")
        predicted_text = predicted_text.replace("\u200c", "")
        transcript = transcript.replace("\u200d", "")
        transcript = transcript.replace("\u200c", "")

        # need to normalize unicode representation for vietnamese
        predicted_text = unicodedata.normalize("NFC", predicted_text)
        transcript = unicodedata.normalize("NFC", transcript)

        # check if there is any word split by "-"
        if "-" in predicted_text:
            predicted_text = check_splitted_words(predicted_text)

        cer = ed.eval(predicted_text, transcript) / float(len(transcript))
        pred_spl = predicted_text.split()
        transcript_spl = transcript.split()

        wer = ed.eval(pred_spl, transcript_spl) / float(len(transcript_spl))
        return cer, wer


def compute_metrics(pred, tgt):
    metrics = ErrorMetrics()

    pred_lines = open(pred, encoding="utf8").readlines()
    tgt_lines = open(tgt, encoding="utf8").readlines()

    predicted = []
    transcripts = []
    for pred_line, tgt_line in zip(pred_lines, tgt_lines):
        if not tgt_line.strip():
            continue
        predicted.append(metrics.preprocess(pred_line))
        transcripts.append(metrics.preprocess(tgt_line))

    cer, wer = metrics.calculate_metrics("\n".join(predicted), "\n".join(transcripts))
    return cer * 100, wer * 100


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--pred", help="Predicted text.")
    parser.add_argument("--tgt", help="Target text.")
    args = parser.parse_args()

    errors = defaultdict(lambda: 0)
    char_counts = defaultdict(lambda: 0)

    metrics = ErrorMetrics()

    pred_lines = open(args.pred, encoding="utf8").readlines()
    tgt_lines = open(args.tgt, encoding="utf8").readlines()

    predicted, transcripts = [], []
    for pred_line, tgt_line in zip(pred_lines, tgt_lines):
        if not tgt_line.strip():
            continue
        predicted.append(metrics.preprocess(pred_line))
        transcripts.append(metrics.preprocess(tgt_line))

    cer, wer = metrics.calculate_metrics("\n".join(predicted), "\n".join(transcripts))
    print("CER {:.2f}".format(cer * 100))
    print("WER {:.2f}".format(wer * 100))
