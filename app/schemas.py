from pydantic import BaseModel
from typing import Optional


class PersonRequest(BaseModel):
    name: str
    age: Optional[int] = None
    address: Optional[str] = None
    work: Optional[str] = None

class PersonResponse(BaseModel):
    id: int
    name: str
    age: Optional[int] = None
    address: Optional[str] = None
    work: Optional[str] = None

    class Config:
        from_attributes = True

class ValidationErrorResponse(BaseModel):
    message: str
    errors: dict[str, str]