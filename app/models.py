from pydantic import BaseModel

class PostStatistics(BaseModel):
    post_id: str
    platform: str
    url: str
    format: str
    likes: int
    views: int
    shares: int = 0
    comment_count: int
    engagement_rate: float

