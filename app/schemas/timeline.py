from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class GeneratedTimelineItem(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=5, max_length=700)
    due_date: date | None = None
    date_type: Literal["official", "recommended", "unknown"] = "unknown"
    source_reference: str | None = None

class TimelineGeneration(BaseModel):
    items: list[GeneratedTimelineItem] = Field(min_length=4, max_length=5)

class TimelinePatch(BaseModel):
    is_completed: bool | None = None
    title: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, min_length=5, max_length=700)
    due_date: date | None = None

class NotesUpdate(BaseModel):
    note: str | None = Field(default=None, max_length=10000)

class TimelineItemOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    application_id: str
    title: str
    description: str
    due_date: date | None = None
    is_completed: bool = False
    sort_order: int
    date_type: str = "unknown"
    source_reference: str | None = None
