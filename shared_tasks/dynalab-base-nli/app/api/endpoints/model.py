from fastapi import APIRouter
from app.domain.model import ModelController
from app.api.schemas.model import ModelSingleInput

router = APIRouter()

@router.get("/")
async def hello():
    model = ModelController()
    text = model.single_evaluation('I hate lambda')
    return {"message": text}

@router.post("/single_evaluation")
async def single_evaluation(data: ModelSingleInput):
    model = ModelController()
    text = model.single_evaluation(data.sourceText, data.origin_lan, data.target_lan)
    return {"message": text}
