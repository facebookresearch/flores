import uuid

import uvicorn
from fastapi import FastAPI
from mangum import Mangum

from app.api.endpoints import helloworld_router, model
app = FastAPI()

app.include_router(helloworld_router.router, prefix='/hello', tags=['hello'])
app.include_router(model.router, prefix='/model', tags=['hello'])

@app.get("/")
def read_root():
    return {"Hello": "Welcome to the jungle"}


handler = Mangum(app)
