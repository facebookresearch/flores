<p align="center">
<img src="flores_logo.png" width="500">
</p>

--------------------------------------------------------------------------------

# Facebook Low Resource MT Benchmark (FLoRes)
FLoRes is a benchmark dataset for machine translation between English and four low resource languages, Nepali, Sinhala, Khmer and Pashto, based on sentences translated from Wikipedia.
The data sets can be downloaded [HERE](https://github.com/facebookresearch/flores/raw/master/data/flores_test_sets.tgz).

**New**: two new languages, Khmer and Pashto, are added to the dataset.

This repository contains data and baselines from the paper:  
[The FLoRes Evaluation Datasets for Low-Resource Machine Translation: Nepali-English and Sinhala-English](https://arxiv.org/abs/1902.01382).

## Baselines

The following instructions will can be used to reproduce the baseline results from the paper.

### Requirements

The baseline uses the
[Indic NLP Library](https://github.com/anoopkunchukuttan/indic_nlp_library) and
[sentencepiece](https://github.com/google/sentencepiece) for preprocessing;
[fairseq](https://github.com/pytorch/fairseq) for model training; and
[sacrebleu](https://github.com/mjpost/sacreBLEU) for scoring.

Dependencies can be installed via pip:
```
$ pip install fairseq sacrebleu sentencepiece
```

The Indic NLP Library will be cloned automatically by the `prepare-{ne,si}en.sh` scripts.

### Download and preprocess data

The `download-data.sh` script can be used to download and extract the raw data.
Thereafter the `prepare-neen.sh` and `prepare-sien.sh` scripts can be used to
preprocess the raw data. In particular, they will use the sentencepiece library
to learn a shared BPE vocabulary with 5000 subword units and binarize the data
for training with fairseq.

To download and extract the raw data:
```
$ bash download-data.sh
```

Thereafter, run the following to preprocess the raw data:
```
$ bash prepare-neen.sh
$ bash prepare-sien.sh
```

### Train a baseline Transformer model

To train a baseline Ne-En model on a single GPU:
```
$ CUDA_VISIBLE_DEVICES=0 fairseq-train \
    data-bin/wiki_ne_en_bpe5000/ \
    --source-lang ne --target-lang en \
    --arch transformer --share-all-embeddings \
    --encoder-layers 5 --decoder-layers 5 \
    --encoder-embed-dim 512 --decoder-embed-dim 512 \
    --encoder-ffn-embed-dim 2048 --decoder-ffn-embed-dim 2048 \
    --encoder-attention-heads 2 --decoder-attention-heads 2 \
    --encoder-normalize-before --decoder-normalize-before \
    --dropout 0.4 --attention-dropout 0.2 --relu-dropout 0.2 \
    --weight-decay 0.0001 \
    --label-smoothing 0.2 --criterion label_smoothed_cross_entropy \
    --optimizer adam --adam-betas '(0.9, 0.98)' --clip-norm 0 \
    --lr-scheduler inverse_sqrt --warmup-updates 4000 --warmup-init-lr 1e-7 \
    --lr 1e-3 --min-lr 1e-9 \
    --max-tokens 4000 \
    --update-freq 4 \
    --max-epoch 100 --save-interval 10
```

To train on 4 GPUs, remove the `--update-freq` flag and run `CUDA_VISIBLE_DEVICES=0,1,2,3 fairseq-train (...)`.
If you have a Volta or newer GPU you can further improve training speed by adding the `--fp16` flag.

This same architecture can be used for En-Ne, Si-En and En-Si:
- For En-Ne, update the training command with:  
  `fairseq-train data-bin/wiki_ne_en_bpe5000 --source-lang en --target-lang ne`
- For Si-En, update the training command with:  
  `fairseq-train data-bin/wiki_si_en_bpe5000 --source-lang si --target-lang en`
- For En-Si, update the training command with:  
  `fairseq-train data-bin/wiki_si_en_bpe5000 --source-lang en --target-lang si`

### Compute BLEU using sacrebleu

Run beam search generation and scoring with sacrebleu:
```
$ fairseq-generate \
    data-bin/wiki_ne_en_bpe5000/ \
    --source-lang ne --target-lang en \
    --path checkpoints/checkpoint_best.pt \
    --beam 5 --lenpen 1.2 \
    --gen-subset valid \
    --remove-bpe=sentencepiece \
    --sacrebleu
```

Note that the `--gen-subset valid` set is the FloRes **dev** set and `--gen-subset test` set is the FloRes **devtest** set.
Replace `--gen-subset valid` with `--gen-subset test` above to score the FLoRes **devtest** set which is corresponding to the reported number in our paper.

**Tokenized BLEU for En-Ne and En-Si:**

For these language pairs we report tokenized BLEU. You can compute tokenized BLEU by removing the `--sacrebleu` flag
from generate.py:
```
$ fairseq-generate \
    data-bin/wiki_ne_en_bpe5000/ \
    --source-lang en --target-lang ne \
    --path checkpoints/checkpoint_best.pt \
    --beam 5 --lenpen 1.2 \
    --gen-subset valid \
    --remove-bpe=sentencepiece
```

### Train iterative back-translation models

After runing the commands in *Download and preprocess data* section above, run the following to download and preprocess the monolingual data:
```
$ bash prepare-monolingual.sh
```

To train the iterative back-translation for two iterations on Ne-En, run the following:
```
$ bash reproduce.sh ne_en
```

The script will train an Ne-En supervised model, translate Nepali monolingual data, train En-Ne back-translation iteration 1 model, translate English monolingual data back to Nepali, and train Ne-En back-translation iteration 2 model. All the model training and data generation happen locally. The script uses all the GPUs listed in `CUDA_VISIBLE_DEVICES` variable unless certain cuda device ids are specified to `train.py`, and it is designed to adjust the hyper-parameters according to the number of available GPUs.  With 8 Tesla V100 GPUs, the full pipeline takes about 25 hours to finish. We expect the final BT iteration 2 Ne-En model achieves around 15.9 (sacre)BLEU score on devtest set. The script supports `ne_en`, `en_ne`, `si_en` and `en_si` directions.

## Citation

If you use this data in your work, please cite:

```bibtex
@inproceedings{,
  title={Two New Evaluation Datasets for Low-Resource Machine Translation: Nepali-English and Sinhala-English},
  author={Guzm\'{a}n, Francisco and Chen, Peng-Jen and Ott, Myle and Pino, Juan and Lample, Guillaume and Koehn, Philipp and Chaudhary, Vishrav and Ranzato, Marc'Aurelio},
  journal={arXiv preprint arXiv:1902.01382},
  year={2019}
}
```

## Changelog
- 2020-04-02: Add two new langauge pairs, Khmer-English, Pashto-English.
- 2019-11-04: Add config to reproduce iterative back-translation result on Sinhala-English and English-Sinhala.
- 2019-10-23: Add script to reproduce iterative back-translation result on Nepali-English and English-Nepali.
- 2019-10-18: Add final test set.
- 2019-05-20: Remove extra carriage return character from Nepali-English parallel dataset.
- 2019-04-18: Specify the linebreak character in the sentencepiece encoding script to fix small portion of misaligned parallel sentences in Nepali-English parallel dataset.
- 2019-03-08: Update tokenizer script to make it compatible with previous version of indic_nlp.
- 2019-02-14: Update dataset preparation script to avoid unexpected extra line being added to each paralel dataset.


## License
The dataset is licenced under CC-BY-SA, see the LICENSE file for details.
