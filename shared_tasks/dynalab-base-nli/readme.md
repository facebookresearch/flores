How to upload a model to dynabench 2.0 :

Extract the model file that a user wishes to upload
    Example: https://dl.fbaipublicfiles.com/flores101/pretrained_models/flores101_mm100_175M.tar.gz
  
Download and extract the Dynabench 2.0 repo: https://models-dynalab.s3.eu-west-3.amazonaws.com/flores_small1/dynalab-base-flores_small1.zip 

Understand the folders:
Inside the repository you will find a folder called app. This folder contains three folders: api, domain, and resources. The api stores some logic you don't need to touch. Resources is empty, and that's the place where you'll want to stote your model's components (i.e. weights, tokenizers, processors, etc.). Finally, the domain folder is where you'll be including your models logic. Specifically, look for the model.py file.

Copy the contents of requirements.txt from the example extracted model and paste them in the Dynabench 2.0 repo requirements.txt 

Single evaluation function:
In this file you will find a class called "ModelController" with only two methods: the class constructor, and a method called "single_evaluation". This is the method you need to update. As its name indicates this method must receive a single example as an input and return a prediction.

Update the app/domain/model.py file which is suitable for the Dynabench 2.0 repo. You can refer to the handler.py from the example model. 
    Note that there are 3 main functions that need to be incorporated:
        Self.preprocess
        Self.inference
        self.postprocess
Remaining files from the example model should be pasted inside the resources folder of dynabench 2.0. 

To Test your model:
You have to run the following commands
    python3 -m venv env
    source env/bin/activate
    python3 -m pip install -r requirements.txt
    python3 -m uvicorn app.app:app --reload
Once you run the last command, open localhost:8000/docs on your favorite browser (i.e. Chrome, Firefox, Brave, etc.). In there, a FastAPI interface should allow you to test the POST request. Click on the single evaluation method, and then on the 'Try it out' button. Finally, fill the request body with your desired input, and click the execute button. Getting a 200 code as a response means you're ready to go!

Upload your model:
Once you're done testing, zip the whole repository. Finally, upload the zip file using the 'Upload model' button down below, and finally click on submit model. Congratulations, you've submitted your model to Dynabench.

**You will need model.pt file to be added in your resource folder