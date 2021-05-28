# Copyright (c) Facebook, Inc. and its affiliates.

import json
import logging
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


# TODO: what are the code for the following langs ???
# ckb (cb_IQ, central Kurdish)
RAW_LANG_MAPPING = (
    "afr:af,amh:am,ara:ar,asm:as,ast:ast,aze:az,bel:be,ben:bn,bos:bs,bul:bg,"
    "cat:ca,ceb:ceb,ces:cs,cym:cy,dan:da,deu:de,ell:el,eng:en,est:et,fas:fa,"
    "fin:fi,fra:fr,ful:ff,gle:ga,glg:gl,guj:gu,hau:ha,heb:he,hin:hi,hrv:hr,"
    "hun:hu,hye:hy,ibo:ig,ind:id,isl:is,ita:it,jav:jv,jpn:ja,kam:kam,kan:kn,"
    "kat:ka,kaz:kk,kea:kea,khm:km,kir:ky,kor:ko,lao:lo,lav:lv,lin:ln,lit:lt,"
    "ltz:lb,lug:lg,luo:luo,mal:ml,mar:mr,mkd:mk,mlt:mt,mon:mn,mri:mi,msa:ms,"
    "mya:my,nep:ne,nld:nl,nob:no,nso:ns,nya:ny,oci:oc,orm:om,ory:or,pan:pa,"
    "pol:pl,por:pt,pus:ps,ron:ro,rus:ru,slk:sk,slv:sl,sna:sn,snd:sd,som:so,"
    "spa:es,srp:sr,swe:sv,swh:sw,tam:ta,tel:te,tgk:tg,tgl:tl,tha:th,tur:tr,"
    "ukr:uk,umb:umb,urd:ur,uzb:uz,vie:vi,wol:wo,xho:xh,yor:yo,zho:zh,"
    "zho_trad:zh,zul:zu"
)


LANG_MAPPING = dict(
    pair.split(":") for pair in RAW_LANG_MAPPING.split(",")  # type: ignore
)


class FakeGenerator:
    """Fake sequence generator, that returns the input."""

    def generate(self, models, sample, prefix_tokens=None):
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
        # M100 uses 2 letter language codes.
        simple_lang = LANG_MAPPING[lang]
        token = self.vocab.index(f"__{simple_lang}__")
        assert token != self.vocab.unk(), f"Unknown language '{lang}' ({simple_lang})"
        return token

    def tokenize(self, line: str) -> list:
        words = self.spm.EncodeAsPieces(line.strip())
        tokens = [self.vocab.index(word) for word in words]
        return tokens

    def preprocess_one(self, sample):
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

    def preprocess(self, data):
        samples = [self.preprocess_one(s["body"]) for s in data]
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

    def postprocess(self, inference_output, data):
        """
        post process inference output into a response.
        response should be a list of json
        the response format will need to pass the validation in
        ```
        dynalab.tasks.flores_small1.TaskIO().verify_response(response)
        ```
        """
        translations = [
            self.vocab.string(tokens, "sentencepiece") for tokens in inference_output
        ]
        return [
            # Signing required by dynabench, don't remove.
            self.taskIO.sign_response(
                {"id": sample["body"]["uid"], "translatedText": translation},
                sample["body"],
            )
            for translation, sample in zip(translations, data)
        ]


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


if __name__ == "__main__":
    from dynalab.tasks import flores_small1

    # TODO: check that the data received from sagemaker/torchserver looks like that.
    data = [{"body": sample} for sample in flores_small1.data]

    manifest = {"model": {"serializedFile": "model.pt"}}
    system_properties = {"model_dir": ".", "gpu_id": None}

    class Context(NamedTuple):
        system_properties: dict
        manifest: dict

    ctx = Context(system_properties, manifest)
    batch_responses = handle(data, ctx)
    print(batch_responses)

    single_responses = [handle([d], ctx)[0] for d in data]
    assert batch_responses == single_responses
