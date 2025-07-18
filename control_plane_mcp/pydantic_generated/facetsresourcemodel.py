# This file was auto-generated. Do not edit manually.
from pydantic import BaseModel, Field
from typing import Any, Optional

class FacetsResourceModel(BaseModel):
    resource_name: str = Field(None, alias='resourceName')
    resource_type: str = Field(None, alias='resourceType')

    class Config:
        validate_by_name = True
        allow_population_by_alias = True
        from_attributes = True