# Copyright (c) Facebook, Inc. and its affiliates.

import torch

import fairseq.checkpoint_utils
import sentencepiece
import json
from pathlib import Path
from dynalab.handler.base_handler import BaseDynaHandler
from dynalab.tasks.flores_small1 import TaskIO
from fairseq.sequence_generator import SequenceGenerator
from fairseq.tasks.translation import TranslationConfig, TranslationTask


class FakeGenerator:
    """Fake sequence generator, that returns the input."""

    def generate(self, models, sample, bos_token):
        return [[{"tokens": sample["net_input"]["src_tokens"][:-1]}]]


class Handler(BaseDynaHandler):
    """Use Fairseq model for translation.
    To use this handler, download one of the Flores pretrained model:

    615M parameters:
        https://dl.fbaipublicfiles.com/flores101/pretrained_models/flores101_mm100_615M.tar.gz
    175M parameters:
        https://dl.fbaipublicfiles.com/flores101/pretrained_models/flores101_mm100_175M.tar.gz

    and extract the files next to this one.
    Notably there should be a "dict.txt" and a "sentencepiece.bpe.model".
    """

    def initialize(self, context):
        """
        load model and extra files.
        """
        model_pt_path, model_file_dir, device = self._handler_initialize(context)
        config = json.loads(
            (Path(model_file_dir) / "model_generation.json").read_text()
        )

        translation_cfg = TranslationConfig()
        self.vocab = TranslationTask.load_dictionary("dict.txt")

        self.spm = sentencepiece.SentencePieceProcessor()
        self.spm.Load("sentencepiece.bpe.model")

        if config.get("dummy", False):
            self.sequence_generator = FakeGenerator()
        else:
            task = TranslationTask(translation_cfg, self.vocab, self.vocab)
            [model], cfg = fairseq.checkpoint_utils.load_model_ensemble(
                [model_pt_path], task=task
            )
            model.eval().to(device)

            self.sequence_generator = SequenceGenerator(
                [model],
                tgt_dict=self.vocab,
                beam_size=config.get("beam_size", 1),
                max_len_a=config.get("max_len_a", 1.3),
                max_len_b=config.get("max_len_b", 5),
                min_len=config.get("min_len", 5),
            )

        self.taskIO = TaskIO()
        self.initialized = True

    def lang_token(self, lang: str) -> int:
        # M100 uses 2 letter language codes.
        simple_lang = lang.split("_")[0]
        token = self.vocab.index(f"__{simple_lang}__")
        assert token != self.vocab.unk(), f"Unknown language '{lang}' ({simple_lang})"
        return token

    def tokenize(self, line: str) -> list:
        words = self.spm.EncodeAsPieces(line.strip())
        tokens = [self.vocab.index(word) for word in words]
        return tokens

    def preprocess(self, data):
        """
        preprocess data into a format that the model can do inference on
        """
        # TODO: this doesn't seem to produce good results. wrong EOS / BOS ?
        sample = self._read_data(data)
        tokens = self.tokenize(sample["sourceText"])
        src_token = self.lang_token(sample["sourceLanguage"])
        sample["net_input"] = {
            "src_tokens": torch.tensor([[src_token] + tokens + [self.vocab.eos()]]),
            "src_lengths": torch.tensor([len(tokens) + 2]),
        }
        tgt_token = self.lang_token(sample["targetLanguage"])
        sample["prefix_tokens"] = torch.tensor([[tgt_token]])
        return sample

    @torch.no_grad()
    def inference(self, input_data: dict) -> list:
        generated = self.sequence_generator.generate(
            models=[],
            sample=input_data,
            prefix_tokens=input_data["prefix_tokens"],
        )
        # `generate` returns a list of samples
        # with several hypothesis per sample
        # and a dict per hypothesis.
        # We also need to strip the language token.
        return generated[0][0]["tokens"][1:]

    def postprocess(self, inference_output, data):
        """
        post process inference output into a response.
        response should be a single element list of a json
        the response format will need to pass the validation in
        ```
        dynalab.tasks.flores_small1.TaskIO().verify_response(response)
        ```
        """
        example = self._read_data(data)
        translation = self.vocab.string(inference_output, "sentencepiece")
        response = {
            "id": example["uid"],
            "translatedText": translation,
        }

        # Required by dynabench, don't remove.
        response = self.taskIO.sign_response(response, example)
        return [response]


_service = Handler()


def handle(data, context):
    if not _service.initialized:
        _service.initialize(context)
    if data is None:
        return None

    input_data = _service.preprocess(data)
    output = _service.inference(input_data)
    response = _service.postprocess(output, data)

    return response
