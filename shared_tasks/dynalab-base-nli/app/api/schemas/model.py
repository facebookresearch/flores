from pydantic import BaseModel

class ModelSingleInput(BaseModel):
    #context: str
    #hypothesis: str
    sourceText: str
    origin_lan: str
    target_lan: str
    
