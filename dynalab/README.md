# Flores on Dynabench

This tutorial should answer those questions.

* How to participate to Flores competition ?
* How to test your model API locally ?
* How to evaluate your your model locally on the dev set ?
* How to make a submission ?


## How to particpate to Flores competition ?

[Flores competition](http://www.statmt.org/wmt21/large-scale-multilingual-translation-task.html)
is made of 3 tracks.

To compete in a track you'll need to submit a model to [Dynabench](https://www.dynabench.org/).
Dynabench will take care of running the inference of the model on the secret test set,
and to publish the resulting metrics to the leaderboard.

## How to test your model API locally ?

Dynabench has certain expectations about the API used by your model.
Dynabench is using [TorchServe](https://pytorch.org/serve/) in the backend.
You'll need to implement a handler that receives a json object representing one translation,
extract the sentence for your model,
and wrap the output of the model in another json obect.
We recommand starting from the example [handler](handler.py)
that should work with most [Fairseq](https://github.com/pytorch/fairseq) models.

You'll need to modify the Handler class for your model.
The `sample` returned by `self._read_data(data)` returns a dict with the following keys:

```py
{
  "uid": "some_unique_identifier",
  "sourceLanguage": "en_XX",
  "targetLanguage": "hr_HR",
  "sourceText": "Hello world !",
}
```


At the end of preprocess you'll need to return a sample like this:

```py
{
  "uid": "some_unique_identifier",
  "sourceLanguage": "en_XX",
  "targetLanguage": "hr_HR",
  "sourceText": "Hello world !",
  "translatedText": "Your translation",
  "signed": "some_hash",
}
```

Note that the "signed" field will be obtain by calling `self.taskIO.sign_response(response, example)`.

Note that you can add edit the [requirements.txt](./requirements.txt) file,
if your model as specific dependencies.

Once you've implemented the handler you'll need to test it locally.

First install `dynalab` using instructions from their [repo](https://github.com/facebookresearch/dynalab#installation).

Then from this directory run:
`dynalab-cli init -n <name_of_your_model>`
Note that the model name need to be lower-kebab-case.

Chose the track you want to apply to: "flores_small1", "flores_small2" or "flores_full".
Note that it doesn't matter for the tests since the input 
format is the same for all tracks.
Then follow the prompt instruction and point to your model path, handler path ...

Then you can run `dynalab-cli test -n <name_of_your_model> --local`


Each track is accompanied with 3 splits of the dataset.
One is the "dev" set that you're encourage to use for validation only.
A "devtest" set which is a public 

    Small Track #1 : 5 Central/East European languages, 30 directions: Croatian, Hungarian, Estonian, Serbian, Macedonian, English

    Small Track #2: 6 East Asian languages, 42 directions: Sundanese, Javanese, Indonesian, Malay, Tagalog, Tamil, English

    Large Track: All Languages, to and from English. Full list at the bottom of this page.



[Dynabench](https://www.dynabench.org/) 
[Flores101]

Flores competition will use Dynabench to run 
the evaluation on the secret test set.

To submit a model to Dynabench you will need to use 
[Dynalab](https://github.com/facebookresearch/dynalab). 

Dynalab 
