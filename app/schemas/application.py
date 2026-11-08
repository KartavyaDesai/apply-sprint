from datetime import date
from pydantic import BaseModel, Field, HttpUrl

class ApplicationCreate(BaseModel):
    university_name: str = Field(min_length=2, max_length=200)
    program_name: str = Field(min_length=2, max_length=200)
    program_url: HttpUrl
    admission_url: HttpUrl | None = None
    application_deadline: date | None = None
    intake: str | None = Field(default=None, max_length=100)
    additional_context: str | None = Field(default=None, max_length=5000)
