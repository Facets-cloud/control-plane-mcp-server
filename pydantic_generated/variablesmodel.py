# This file was auto-generated. Do not edit manually.
from pydantic import BaseModel, Field
from typing import Any, Optional

class VariablesModel(BaseModel):
    description: str = None
    global_: bool = Field(None, alias='global')
    secret: bool = None
    status: str = None
    value: str = None

    class Config:
        validate_by_name = True
        allow_population_by_alias = True
        from_attributes = True