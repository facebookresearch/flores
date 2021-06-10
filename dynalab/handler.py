# Copyright (c) Facebook, Inc. and its affiliates.

import json
import logging
import time
import os
from pathlib import Path

import fairseq.checkpoint_utils
import sentencepiece
import torch
from typing import NamedTuple
from dynalab.handler.base_handler import BaseDynaHandler
from dynalab.tasks.flores_small1 import TaskIO
from fairseq.sequence_generator import SequenceGenerator
from fairseq.tasks.translation import TranslationConfig, TranslationTask
from fairseq.data import data_utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tell Torchserve to let use do the deserialization
os.environ["TS_DECODE_INPUT_REQUEST"] = "false"


def mapping(languages: str) -> dict:
    return dict(
        tuple(pair.split(":"))
        for pair in languages.strip().replace("\n", "").split(",")
    )


ISO2M100 = mapping(
    """
afr:af,amh:am,ara:ar,asm:as,ast:ast,azj:az,bel:be,ben:bn,bos:bs,bul:bg,
cat:ca,ceb:ceb,ces:cs,ckb:ku,cym:cy,dan:da,deu:de,ell:el,eng:en,est:et,
fas:fa,fin:fi,fra:fr,ful:ff,gle:ga,glg:gl,guj:gu,hau:ha,heb:he,hin:hi,
hrv:hr,hun:hu,hye:hy,ibo:ig,ind:id,isl:is,ita:it,jav:jv,jpn:ja,kam:kam,
kan:kn,kat:ka,kaz:kk,kea:kea,khm:km,kir:ky,kor:ko,lao:lo,lav:lv,lin:ln,
lit:lt,ltz:lb,lug:lg,luo:luo,mal:ml,mar:mr,mkd:mk,mlt:mt,mon:mn,mri:mi,
msa:ms,mya:my,nld:nl,nob:no,npi:ne,nso:ns,nya:ny,oci:oc,orm:om,ory:or,
pan:pa,pol:pl,por:pt,pus:ps,ron:ro,rus:ru,slk:sk,slv:sl,sna:sn,snd:sd,
som:so,spa:es,srp:sr,swe:sv,swh:sw,tam:ta,tel:te,tgk:tg,tgl:tl,tha:th,
tur:tr,ukr:uk,umb:umb,urd:ur,uzb:uz,vie:vi,wol:wo,xho:xh,yor:yo,zho_simp:zh,
zho_trad:zh,zul:zu
"""
)


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
        config = json.loads(
            (Path(model_file_dir) / "model_generation.json").read_text()
        )
        self.device = device

        translation_cfg = TranslationConfig()
        self.vocab = TranslationTask.load_dictionary("dict.txt")

        self.spm = sentencepiece.SentencePieceProcessor()
        self.spm.Load("sentencepiece.bpe.model")
        logger.info("Loaded sentencepiece.bpe.model")

        if config.get("dummy", False):
            self.sequence_generator = FakeGenerator()
            logger.warning("Will use a FakeGenerator model, only testing BPE")
        else:
            task = TranslationTask(translation_cfg, self.vocab, self.vocab)
            [model], cfg = fairseq.checkpoint_utils.load_model_ensemble(
                [model_pt_path], task=task
            )
            model.eval().to(self.device)
            logger.info(f"Loaded model from {model_pt_path} to device {self.device}")
            logger.info(
                f"Will use the following config: {json.dumps(config, indent=4)}"
            )
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
        """Converts the ISO 639-3 language code to MM100 language codes."""
        simple_lang = ISO2M100[lang]
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
        # TODO: this doesn't seem to produce good results. wrong EOS / BOS ?
        tokens = self.tokenize(sample["sourceText"])
        src_token = self.lang_token(sample["sourceLanguage"])
        tgt_token = self.lang_token(sample["targetLanguage"])
        return {
            "src_tokens": [src_token] + tokens + [self.vocab.eos()],
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
        return [
            # Signing required by dynabench, don't remove.
            self.taskIO.sign_response(
                {"id": sample["uid"], "translatedText": translation},
                sample,
            )
            for translation, sample in zip(translations, samples)
        ]


_service = Handler()


def deserialize(torchserve_data: list) -> list:
    samples = []
    for torchserve_sample in torchserve_data:
        data = torchserve_sample["body"]
        # In case torchserve did the deserialization for us.
        if isinstance(data, dict):
            samples.append(data)
        elif isinstance(data, (bytes, bytearray)):
            lines = data.decode("utf-8").splitlines()
            for i, l in enumerate(lines):
                try:
                    samples.append(json.loads(l))
                except Exception as e:
                    logging.error(f"Couldn't deserialize line {i}: {l}")
                    logging.exception(e)
        else:
            logging.error(f"Unexpected payload: {data}")

    return samples


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
    all_samples = deserialize(torchserve_data)
    n = len(all_samples)
    logger.info(
        f"Deserialized a batch of size {n} ({n/(time.time()-start_time):.2f} samples / s)"
    )
    # Adapt this to your model. The GPU has 16Gb of RAM.
    batch_size = 128
    results = []
    samples = []
    for i, sample in enumerate(all_samples):
        samples.append(sample)
        if len(samples) < batch_size and i + 1 < n:
            continue

        results.extend(handle_mini_batch(_service, samples))
        samples = []

    assert len(results)
    start_time = time.time()
    response = "\n".join(json.dumps(r, indent=None, ensure_ascii=False) for r in results)
    logger.info(
        f"Serialized a batch of size {n} ({n/(time.time()-start_time):.2f} samples / s)"
    )
    return [response]


def local_test():
    from dynalab.tasks import flores_small1

    bin_data = b"\n".join(json.dumps(d).encode("utf-8") for d in flores_small1.data)
    torchserve_data = [{"body": bin_data}]

    manifest = {"model": {"serializedFile": "model.pt"}}
    system_properties = {"model_dir": ".", "gpu_id": None}

    class Context(NamedTuple):
        system_properties: dict
        manifest: dict

    ctx = Context(system_properties, manifest)
    batch_responses = handle(torchserve_data, ctx)
    print(batch_responses)

    single_responses = [
        handle([{"body": json.dumps(d).encode("utf-8")}], ctx)[0]
        for d in flores_small1.data
    ]
    assert batch_responses == ["\n".join(single_responses)]


if __name__ == "__main__":
    local_test()
