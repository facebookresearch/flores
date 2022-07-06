# Flores on Dynabench

This tutorial should answer the following questions.

* How to participate in the FLORES-101 Large-Scale Multilingual Machine Translation Shared Task?
* How to test your model API locally?
* How to evaluate your your model locally on the dev/devtest set?
* How to make a submission?


## Participating in the FLORES-101 WMT 2021 Shared Task

The [Large-Scale Multilingual Machine Translation Shared Task](http://www.statmt.org/wmt21/large-scale-multilingual-translation-task.html)
comprises of 3 tracks.

Small Track #1 : 5 Central/East European languages, 30 directions: Croatian, Hungarian, Estonian, Serbian, Macedonian, English

Small Track #2: 5 East Asian languages, 30 directions: Javanese, Indonesian, Malay, Tagalog, Tamil, English

Large Track: All Languages, to and from English. Full list at the bottom of this page.

To compete in a track you'll need to submit a model to [Dynabench](https://www.dynabench.org/flores).
Dynabench will take care of running the inference of the model on the secret test set and will publish the resulting metrics to the leaderboard.


## Evaluate your model locally on the dev/devtest set

Each track is accompanied with 3 splits of the dataset.
* a public `dev` set that you're encouraged to use for validation and selecting
hyper-parameters.
* a public `devtest` set which you can use as a test set
* and a secret `test` set which will be used by Dynabench to evaluate your model.

The simplest way to get started is to train and evaluate your model using the dev 
and the devtest dataset which have been released publicly.

The [main README](../flores#evaluation) has more instructions on evaluating your model locally.


## Testing your model API locally

Dynabench has certain expectations about the API used by your model.
Dynalab provides tools for testing and uploading the model to Dynabench.
The documentation below provides an overview for interacting with Dynalab and should 
suffice for testing the model API. Please refer to the [README](https://github.com/facebookresearch/dynalab) 
for more details.

Dynabench uses [TorchServe](https://pytorch.org/serve/) in the backend.
You'll need to implement a handler that:
* receives several json objects (one per line) representing one batch of translation
* extract the sentences for your model
* compute the translations
* returns translations in json objects (one per line)

We recommend starting from the example [handler](handler.py)
that should work with most [Fairseq](https://github.com/pytorch/fairseq) models.

You'll need to modify the Handler class for your model.
We recommend against modifying the other top level functions.
Note how `__init__` method is able to load the local files.

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

Note that the "signed" field will be obtained by calling `self.taskIO.sign_response(response, example)`.

Also note that you can edit the [requirements.txt](./requirements.txt) file,
based your model's specific dependencies.

Once you've implemented the handler you'll need to test it locally.

First install `dynalab` using instructions from their [repo](https://github.com/facebookresearch/dynalab#installation).

The simplest test is to run `python handler.py`.
You'll need to update the `local_test` function to use the task you want.
Then you can move to running more involved tests using Dynalab.

Afterwards, from this directory run:
`dynalab-cli init -n <name-of-your-model>`
Note that the model name needs to be lower-kebab-case.

Chose the track you want to apply to: "flores_small1", "flores_small2" or "flores_full".
Note that the input format is same for all the tracks.
Then follow the prompt instruction and point to your model path, handler path ...

Then you can run `dynalab-cli test -n <name-of-your-model> --local`
This will run your model on a sample input, using your current python environment.
For debugging you can run:
`python -m pdb $(which dynalab-cli) test -n <name-of-your-model> --local`

If this works, you can then proceed to the docker tests.
This will create a full docker image and run the tests inside it.
This example can be used to check if `requirements.txt`
contains all the dependencies needed to run your model.

`dynalab-cli test -n <name-of-your-model>`

## Making a submission

To make a submission you'll need to create an account on [Dynabench](https://www.dynabench.org/).
And login locally using `dynalab-cli login`.

Then you can finally run `dynalab-cli upload -n <name-of-your-model>`.
You'll receive a confirmation email afterwards.
