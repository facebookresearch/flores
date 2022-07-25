# Copyright (c) Facebook, Inc. and its affiliates.

import collections
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import NamedTuple

sys.path.append("/home/model-server/code/fairseq")
import fairseq.checkpoint_utils
import sentencepiece
import torch
from dynalab.handler.base_handler import BaseDynaHandler
from dynalab.tasks.task_io import TaskIO
from fairseq.data import data_utils
from fairseq.sequence_generator import SequenceGenerator
from fairseq.tasks.translation import TranslationConfig, TranslationTask

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tell Torchserve to let us do the deserialization
os.environ["TS_DECODE_INPUT_REQUEST"] = "false"


def mt_postprocess(input, lang):
    if lang == "zho_simp":
        return zh_postprocess(input)
    return input


QUOTES = re.compile(r'"|,,|\'\'|``|‟|“|”')
HYPHEN = re.compile(r" -\s*- ")
STARTQUOTE = re.compile(r'(^|[ ({\[])("|,,|\'\'|``)')
ENDQUOTE = re.compile(r'("|\'\'|‟)($|[ ,.?!:;)}\]])')
NUMERALS = re.compile(r"([\d]+[\d\-\.%\,:]*)")
LATIN = re.compile(r"([a-zA-Z’\'@]+[a-zA-Z’\'@_:\-]*)")
SPACE = re.compile(r"\s+")
PUNCT = re.compile(r"\s([\.)”。])")
PUNCT2 = re.compile(r"([(“])\s")
COMMA1 = re.compile(r"(\D),")
COMMA2 = re.compile(r",(\D)")
# Don't replace multiple dots 
DOT = re.compile(r"(?<!\.)\.(?![\d\.])")
# Don't replace ':' that were part of Latin word/number
COLON = re.compile(r":(?![\da-zA-Z])")


def zh_postprocess(input):
    if len(QUOTES.findall(input)) == 2:
        s = QUOTES.split(input)
        input = "{}“{}”{}".format(s[0], s[1], s[2])
    if len(QUOTES.findall(input)) == 4:
        s = QUOTES.split(input)
        input = "{}“{}”{}“{}”{}".format(s[0], s[1], s[2], s[3], s[4])

    input = STARTQUOTE.sub(r"“\1", input)
    input = ENDQUOTE.sub(r"\2“", input)
    input = HYPHEN.sub(r"——", input)
    input = SPACE.sub(r" ", input)
    input = PUNCT.sub(r"\1", input)
    input = PUNCT2.sub(r"\1", input)
    input = DOT.sub("。", input)
    input = COLON.sub("：", input)
    input = COMMA1.sub(r"\1，", input)
    input = COMMA2.sub(r"，\1", input)
    input = input.replace("?", "？")
    input = input.replace("!", "！")
    input = input.replace(";", "；")
    input = input.replace("(", "（")
    input = input.replace(")", "）")

    return input.strip()


def test_chinese_colon(*_):
    # en_source = "The molar ratio of E:S:M in the lipid bilayer is approximately 1:20:300."
    zh_reference = "脂质双分子层中 E:S:M 的摩尔比约为 1:20:300。"
    zh_translated = "脂质双分子层中E:S:M的摩尔比约为1:20:300."
    assert zh_translated != zh_reference
    zh_fixed = zh_postprocess(zh_translated)
    assert "E:S:M" in zh_fixed
    assert "1:20:300" in zh_fixed
    assert zh_fixed == zh_reference


class FakeGenerator:
    """Fake sequence generator, that returns the input."""

    def generate(self, models, sample, prefix_tokens=None):
        src_tokens = sample["net_input"]["src_tokens"]
        return [[{"tokens": tokens[:-1]}] for tokens in src_tokens]


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
        logger.info(
            f"Will initialize with system_properties: {context.system_properties}"
        )
        model_pt_path, model_file_dir, device = self._handler_initialize(context)
        self.device = device
        config = json.loads(
            (Path(model_file_dir) / "model_generation.json").read_text()
        )
        directions = config.get("directions")
        self.supported_directions = set(directions) if directions else None

        translation_cfg = TranslationConfig()
        self.vocab = TranslationTask.load_dictionary(
            str(Path(model_file_dir) / "dict.txt")
        )

        spm_path = config.get("sentencepiece", "sentencepiece.bpe.model")
        self.spm = sentencepiece.SentencePieceProcessor()
        self.spm.Load(spm_path)
        logger.info(f"Loaded {spm_path}")

        if config.get("dummy", False):
            self.sequence_generator = FakeGenerator()
            logger.warning("Will use a FakeGenerator model, only testing SPM")
        else:
            task = TranslationTask(translation_cfg, self.vocab, self.vocab)
            [model], cfg = fairseq.checkpoint_utils.load_model_ensemble(
                [model_pt_path], task=task
            )
            model.eval().to(self.device)
            self.model = model
            logger.info(f"Loaded model from {model_pt_path} to device {self.device}")
            if "gpu" in self.device:
                logger.info("Will use fp16")
                model.half()
            logger.info(
                f"Will use the following config: {json.dumps(config, indent=4)}"
            )
            self.sequence_generator = SequenceGenerator(
                [model], tgt_dict=self.vocab, **config["generation"]
            )

        self.taskIO = TaskIO("flores_small1")
        self.initialized = True

    def lang_token(self, lang: str) -> int:
        """Converts the ISO 639-3 language code to MM100 language codes."""
        simple_lang = "zho_Hans" if lang == "zho_simp" else lang
        token = self.vocab.index(f"__{simple_lang}__")
        assert token != self.vocab.unk(), f"Unknown language '{lang}' ({simple_lang})"
        return token

    def tokenize(self, line: str) -> list:
        words = self.spm.EncodeAsPieces(line.strip())
        tokens = [self.vocab.index(word) for word in words]
        return tokens

    def preprocess_one(self, sample) -> dict:
        """
        preprocess data into a format that the model can do inference on
        """
        tokens = self.tokenize(sample["sourceText"])
        # src_token = self.lang_token(sample["sourceLanguage"])
        tgt_token = self.lang_token(sample["targetLanguage"])
        return {
            "src_tokens": [tgt_token] + tokens + [self.vocab.eos()],
            "src_length": len(tokens) + 1,
            "tgt_token": tgt_token,
        }
        return sample

    def preprocess(self, samples) -> dict:
        samples = [self.preprocess_one(s) for s in samples]
        prefix_tokens = torch.tensor([[s["tgt_token"]] for s in samples])
        src_lengths = torch.tensor([s["src_length"] for s in samples])
        src_tokens = data_utils.collate_tokens(
            [torch.tensor(s["src_tokens"]) for s in samples],
            self.vocab.pad(),
            self.vocab.eos(),
        )
        return {
            "nsentences": len(samples),
            "ntokens": src_lengths.sum().item(),
            "net_input": {
                "src_tokens": src_tokens.to(self.device),
                "src_lengths": src_lengths.to(self.device),
            },
            "prefix_tokens": prefix_tokens.to(self.device),
        }

    def strip_pad(self, sentence):
        assert sentence.ndim == 1
        return sentence[sentence.ne(self.vocab.pad())]

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
        return [hypos[0]["tokens"][1:] for hypos in generated]

    def postprocess(self, inference_output, samples: list) -> list:
        """
        post process inference output into a response.
        response should be a list of json
        the response format will need to pass the validation in
        ```
        dynalab.tasks.flores_small1.TaskIO().verify_response(response)
        ```
        """
        translations = [
            self.vocab.string(self.strip_pad(sentence), "sentencepiece")
            for sentence in inference_output
        ]
        responses = [
            {
                "id": sample["uid"],
                "translatedText": mt_postprocess(translation, sample["targetLanguage"]),
            }
            for translation, sample in zip(translations, samples)
        ]
        # Signing required by dynabench, don't remove.
        for response, sample in zip(responses, samples):
            self.taskIO.sign_response(response, sample)
        return responses

    def accepts(self, sample) -> bool:
        if not self.supported_directions:
            return True

        direction = "-".join((sample["sourceLanguage"], sample["targetLanguage"]))
        return direction in self.supported_directions

    def ignore_sample(self, sample) -> dict:
        r = {"id": sample["uid"], "translatedText": ""}
        self.taskIO.sign_response(r, sample)
        return r


_service = Handler()


def deserialize(torchserve_data: list) -> tuple:
    samples = []
    sample2batch = {}
    for batch_id, torchserve_sample in enumerate(torchserve_data):
        data = torchserve_sample["body"]
        # In case torchserve did the deserialization for us.
        if isinstance(data, dict):
            sample2batch[data["uid"]] = batch_id
            samples.append(data)
        elif isinstance(data, (bytes, bytearray)):
            lines = data.decode("utf-8").splitlines()
            for i, l in enumerate(lines):
                try:
                    sample = json.loads(l)
                    sample2batch[sample["uid"]] = batch_id
                    samples.append(sample)
                except Exception as e:
                    logging.error(f"Couldn't deserialize line {i}: {l}")
                    logging.exception(e)
        else:
            logging.error(f"Unexpected payload: {data}")

    return samples, len(torchserve_data), sample2batch


def handle_mini_batch(service, samples):
    n = len(samples)
    start_time = time.time()
    input_data = service.preprocess(samples)
    logger.info(
        f"Preprocessed a batch of size {n} ({n/(time.time()-start_time):.2f} samples / s)"
    )

    start_time = time.time()
    output = service.inference(input_data)
    logger.info(
        f"Infered a batch of size {n} ({n/(time.time()-start_time):.2f} samples / s)"
    )

    start_time = time.time()
    json_results = service.postprocess(output, samples)
    logger.info(
        f"Postprocessed a batch of size {n} ({n/(time.time()-start_time):.2f} samples / s)"
    )
    return json_results


def handle(torchserve_data, context):
    if not _service.initialized:
        _service.initialize(context)
    if torchserve_data is None:
        return None

    start_time = time.time()
    all_samples, num_batches, sample2batch = deserialize(torchserve_data)
    n = len(all_samples)
    logger.info(
        f"Deserialized a batch of size {n} ({n/(time.time()-start_time):.2f} samples / s)"
    )
    # Adapt this to your model. The GPU has 11Gb of RAM.
    batch_size = 96
    results = []
    samples = []
    for i, sample in enumerate(all_samples):
        if not _service.accepts(sample):
            results.append(_service.ignore_sample(sample))
            continue

        samples.append(sample)
        if len(samples) < batch_size:
            continue

        results.extend(handle_mini_batch(_service, samples))
        samples = []
    if len(samples) > 0:
        results.extend(handle_mini_batch(_service, samples))
        samples = []

    assert len(results)

    return wrap_as_batches(results, num_batches, sample2batch)


def wrap_as_batches(results, num_batches, sample2batch):
    start_time = time.time()
    n = len(sample2batch)
    if num_batches == 1:
        response = "\n".join(
            json.dumps(r, indent=None, ensure_ascii=False) for r in results
        )
        logger.info(
            f"Serialized a batch of size {n} ({n/(time.time()-start_time):.2f} samples / s)"
        )
        return [response]

    batch2results = collections.defaultdict(list)
    for result in results:
        batch_id = sample2batch[result["id"]]
        batch2results[batch_id].append(result)

    responses = []
    for batch_id in sorted(batch2results.keys()):
        response = "\n".join(
            json.dumps(r, indent=None, ensure_ascii=False)
            for r in batch2results[batch_id]
        )
        responses.append(response)
    logger.info(
        f"Serialized a batch of size {n} ({n/(time.time()-start_time):.2f} samples / s)"
    )
    return responses


def mk_sample(text, tgt, i=0):
    return {
        "uid": f"sample{i}",
        "sourceText": text,
        "sourceLanguage": "eng",
        "targetLanguage": tgt,
    }


class Context(NamedTuple):
    system_properties: dict
    manifest: dict

    def _call_handler(self, data):
        need_wrap = not isinstance(data, list)
        if need_wrap:
            data = [data]
        bin_data = b"\n".join(json.dumps(d).encode("utf-8") for d in data)
        torchserve_data = [{"body": bin_data}]
        responses = handle(torchserve_data, self)
        parsed_responses = [
            json.loads(l)["translatedText"] for l in responses[0].splitlines()
        ]
        if need_wrap:
            return parsed_responses[0]
        else:
            return parsed_responses


def local_test():
    from dynalab.tasks.task_io import TaskIO

    manifest = {"model": {"serializedFile": "checkpoint.pt"}}
    system_properties = {"model_dir": ".", "gpu_id": 0}
    ctx = Context(system_properties, manifest)
    for k, testcase in globals().items():
        if k.startswith("test_") and callable(testcase):
            logger.info(f"[TESTCASE] {k}")
            testcase(ctx)


def test_no_unk(ctx):
    en_src = "a gazetteer compiled by Chang Qu (常璩) during the Western Jin Dynasty"
    isl_ref = "lögbók sem Chang Qu (常璩) tók saman á tímum Vestur-Jin-keisaraættarinnar"
    isl_translated = ctx._call_handler(mk_sample(en_src, "isl"))
    assert "<unk>" not in isl_translated
    # 璩 is really not part of the dict so we can't generate it.
    # assert "(常璩)" in isl_translated
    # assert isl_ref == isl_translated


def test_batching(ctx):
    JAZZ = """
Jazz is a music genre that originated in the African-American communities of New Orleans, Louisiana, United States, in the late 19th and early 20th centuries, with its roots in blues and ragtime.
Since the 1920s Jazz Age, it has been recognized as a major form of musical expression in traditional and popular music, linked by the common bonds of African-American and European-American musical parentage.
Jazz is characterized by swing and blue notes, complex chords, call and response vocals, polyrhythms and improvisation.
Jazz has roots in West African cultural and musical expression, and in African-American music traditions.
""".strip().splitlines()
    mock_data = [
        mk_sample(line, lang, i)
        for lang in ["oci", "lug", "zul", "ibo", "zho_simp", "isl", "hau"]
        for i, line in enumerate(JAZZ)
    ]

    batch_responses = ctx._call_handler(mock_data)
    print("==== batch ====")
    print("\n".join(batch_responses))
    single_responses = [ctx._call_handler(d) for d in mock_data]
    print("==== one by one ====")
    print("\n".join(single_responses))
    assert batch_responses == single_responses


if __name__ == "__main__":
    local_test()
