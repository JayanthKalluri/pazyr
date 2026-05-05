from pydantic import BaseModel
from datetime import datetime
from typing import List, Literal, Dict

class Website(BaseModel):
    name: str
    type: Literal["pdf", "html"] | None
    url: str | None = None

class Artifact(BaseModel):
    id: str
    title: str
    summary: str
    published: datetime
    location: str | None = None
    url: str
    source: str

class JobObject(BaseModel):
    artifact: Artifact
    id: str
    created_at: datetime
    
class ScheduledCrawlJob(BaseModel):
    start_date: datetime