# Flores on Dynabench

This tutorial should answer those questions.

* How to participate to Flores competition ?
* How to test your model API locally ?
* How to evaluate your your model locally on the dev/devtest set ?
* How to make a submission ?


## How to particpate to Flores competition ?

[Flores competition](http://www.statmt.org/wmt21/large-scale-multilingual-translation-task.html)
is made of 3 tracks.

Small Track #1 : 5 Central/East European languages, 30 directions: Croatian, Hungarian, Estonian, Serbian, Macedonian, English

Small Track #2: 5 East Asian languages, 30 directions: Javanese, Indonesian, Malay, Tagalog, Tamil, English

Large Track: All Languages, to and from English. Full list at the bottom of this page.

To compete in a track you'll need to submit a model to [Dynabench](https://www.dynabench.org/).
Dynabench will take care of running the inference of the model on the secret test set,
and to publish the resulting metrics to the leaderboard.


## How to evaluate your your model locally on the dev/devtest set ?

Each track is accompanied with 3 splits of the dataset.
* a public `dev` set that you're encourage to use for validation and selecting
hyper-parameters.
* a public `devtest` set which you can use as a test set
* and a secret `test` set which will be used by Dynabench to evaluate your model.

The simplest way to get started is to train and evaluate your model using the dev 
and devtest dataset which have been released publicly.

The [main README](../flores#evaluation) has more instructions on how to do this.


## How to test your model API locally ?

Dynabench has certain expectations about the API used by your model.
Dynalab provide tools to test and upload model to Dynabench.
The documentation below should be enough to interact with Dynalab,
but you can read [their README](https://github.com/facebookresearch/dynalab)
for more details.

Dynabench is using [TorchServe](https://pytorch.org/serve/) in the backend.
You'll need to implement a handler that:
* receives several json objects (one per line) representing one batch of translation
* extract the sentences for your model
* compute the translations
* returns translations in json objects (one per line)

We recommand starting from the example [handler](handler.py)
that should work with most [Fairseq](https://github.com/pytorch/fairseq) models.

You'll need to modify the Handler class for your model.
We recommand against modifying the other top level functions.
Note how `__init__` method is able to load at the local files.

Each `sample` passed to `service.preprocess` is a dict with the following keys:

```py
{
  "uid": "some_unique_identifier",
  "sourceLanguage": "eng",
  "targetLanguage": "hrv",
  "sourceText": "Hello world !",
}
```


At the end of preprocess you'll need to return a list of sample like this:

```py
{
  "uid": "some_unique_identifier",
  "translatedText": "Your translation",
  "signed": "some_hash",
}
```

Note that the "signed" field will be obtain by calling `self.taskIO.sign_response(response, example)`.

Note that you can add edit the [requirements.txt](./requirements.txt) file,
if your model as specific dependencies.

Once you've implemented the handler you'll need to test it locally.

First install `dynalab` using instructions from their [repo](https://github.com/facebookresearch/dynalab#installation).

The simplest test is to run `python handler.py`.
You'll need to update the `local_test` function to use the task you want.
Then you can move to the more involved tests using Dynalab.

Then from this directory run:
`dynalab-cli init -n <name-of-your-model>`
Note that the model name need to be lower-kebab-case.
The first time you do this, 

Chose the track you want to apply to: "flores_small1", "flores_small2" or "flores_full".
Note that the input format is the same for all tracks.
Then follow the prompt instruction and point to your model path, handler path ...

Then you can run `dynalab-cli test -n <name-of-your-model> --local`
This will run your model on a sample input, using your current python environment.
To debug you can also run:
`python -m pdb $(which dynalab-cli) test -n <name-of-your-model> --local`

If this work, you can then proceed to the docker tests.
This will create a full docker image and run the tests inside it.
This for example allows to check that the `requirements.txt` file
contains everything needed to run your model.

`dynalab-cli test -n <name-of-your-model>`

## How to make a submission ?

To make a submission you'll need to create an account on [Dynabench](https://www.dynabench.org/).
And login locally using `dynalab-cli login`.

Then you can finally run `dynalab-cli upload -n <name-of-your-model>`.
You'll receive a confirmation email afterwards.
