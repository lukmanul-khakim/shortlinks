from pydantic import BaseModel, HttpUrl


class CreateLinkRequest(BaseModel):
    url: HttpUrl


class LinkResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str


class StatsResponse(BaseModel):
    short_code: str
    original_url: str
    clicks: int
