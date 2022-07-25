import json
import logging
from pathlib import Path
# sys.path.append("./app/resources/fairseq")
import fairseq.checkpoint_utils
import sentencepiece
import torch

from fairseq.data import data_utils
from fairseq.sequence_generator import SequenceGenerator
from fairseq.tasks.translation import TranslationConfig, TranslationTask

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModelController:
    def __init__(self) -> None:
        # copy from initialize()
        """
                load model and extra files.
                """
        config = json.loads(
            (Path("app/resources") / "model_generation.json").read_text()
        )
        # directions = config.get("directions")
        # self.supported_directions = set(directions) if directions else None

        translation_cfg = TranslationConfig()
        self.vocab = TranslationTask.load_dictionary(
            str(Path("app/resources") / "dict.txt")
        )

        spm_path = "app/resources/sentencepiece.bpe.model"
        self.spm = sentencepiece.SentencePieceProcessor()
        self.spm.Load(spm_path)
        logger.info(f"Loaded {spm_path}")
        self.model_pt_path = "app/resources/model.pt"
        task = TranslationTask(translation_cfg, self.vocab, self.vocab)
        [model], cfg = fairseq.checkpoint_utils.load_model_ensemble(
            [self.model_pt_path], task=task
        )
        self.device = "cpu"
        model.eval().to(self.device)
        self.model = model
        logger.info(f"Loaded model from {self.model_pt_path} to device {self.device}")
        if "gpu" in self.device:
            logger.info("Will use fp16")
            model.half()
        logger.info(
            f"Will use the following config: {json.dumps(config, indent=4)}"
        )
        self.sequence_generator = SequenceGenerator(
            [model], tgt_dict=self.vocab, **config["generation"]
        )
        # self.device = torch.device("cpu")

    def single_evaluation(self, sourceText: str, origin_lan: str, target_lan: str):
        """
        sourceText = "Hello world !"
        origin_lan = "eng"
        target_lan = "est" # estonian
        """
        sample = {"sourceText": sourceText, "sourceLanguage": origin_lan, "targetLanguage": target_lan}
        samples: list[dict] = self.preprocess([sample])
        print("samples:", samples)
        tokens: list[list[int]] = self.inference(samples)
        print("tokens:", tokens)
        translations: list[str] = self.postprocess(tokens)

        return {"translatedText": translations[0]}

    def preprocess(self, samples: list[dict]) -> dict:
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

    def preprocess_one(self, sample) -> dict:
        """
        preprocess data into a format that the model can do inference on
        """
        tokens = self.tokenize(sample["sourceText"])
        src_token = self.lang_token(sample["sourceLanguage"])
        tgt_token = self.lang_token(sample["targetLanguage"])
        return {
            "src_tokens": [src_token] + tokens + [self.vocab.eos()],
            "src_length": len(tokens) + 1,
            "tgt_token": tgt_token,
        }

    def tokenize(self, line: str) -> list:
        words = self.spm.EncodeAsPieces(line.strip())
        tokens = [self.vocab.index(word) for word in words]
        return tokens

    def lang_token(self, lang: str) -> int:
        """Converts the ISO 639-3 language code to MM100 language codes."""
        # simple_lang = "zho_Hans" if lang == "zho_simp" else lang
        token = self.vocab.index(f"__{lang}__")
        # assert token != self.vocab.unk(), f"Unknown language '{lang}' ({lang})"
        return token

    @torch.no_grad()
    def inference(self, input_data: dict) -> list[int]:
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

    def postprocess(self, inference_output) -> list:
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
        return translations

    def strip_pad(self, sentence):
        assert sentence.ndim == 1
        return sentence[sentence.ne(self.vocab.pad())]


if __name__ == '__main__':
    response = ModelController().single_evaluation('hello world', 'eng', "est")
    print(response)
