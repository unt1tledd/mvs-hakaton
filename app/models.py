from datetime import datetime
from pydantic import BaseModel
from typing import Union

class Post(BaseModel):
    post_id: int
    platform: str
    format: str
    date: Union[datetime, str]  # Может быть datetime или строка

    likes: int = 0
    shares: int = 0
    comment_count: int = 0
    views: int = 0

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class VKPost(Post):
    owner_id: int
    reposts: int = 0
    polls_participation: int = 0