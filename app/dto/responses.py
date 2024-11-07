from pydantic import BaseModel, ConfigDict


class CrawlerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    message: str


class GetLinksResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    links: list[str]
