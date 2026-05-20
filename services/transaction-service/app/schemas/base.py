from pydantic import BaseModel, ConfigDict


class ModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
