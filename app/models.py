from pydantic import BaseModel

class PostStatistics(BaseModel):
    post_id: str
    platform: str
    url: str
    format: str
    likes: int = 0
    views: int = 0
    shares: int = 0
    comment_count: int = 0
    engagement_rate: float
