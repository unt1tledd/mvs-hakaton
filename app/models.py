from datetime import datetime
from pydantic import BaseModel

class Post(BaseModel):
    post_id: int
    platform: str
    format: str
    date: datetime

    likes: int = 0
    shares: int = 0
    comment_count: int = 0
    views: int = 0

class VKPost(Post):
    owner_id: int
    reposts: int = 0
    polls_participation: int = 0