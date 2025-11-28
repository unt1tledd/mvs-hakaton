from fastapi import FastAPI, HTTPException, APIRouter
from .utils import get_mws_posts, find_post, post_db

app = FastAPI()
router = APIRouter()

@app.get("/{post_id}/{field}")
def get_field(post_id: int, field: str) :
    """ Getter для всех полей """

    if not post_db:
        get_mws_posts()

    post = find_post(post_id)
    if not post:
        raise HTTPException(404, f"Not Found post with id: {post_id}")
    
    if not hasattr(post, field):
        raise HTTPException(400, f"Field '{field}' does not exist")

    return getattr(post, field)

@router.get("/content")
def get_content():
    """ Возвращает список постов из MWS Tables """

    return get_mws_posts()

@router.get("/top_posts")
def top_posts(field: str, limit: int = 10, descending: bool = True):
    """ Возвращает топ постов по указанному полю """

    if not post_db:
        get_mws_posts()

    if not hasattr(post_db, field):
        return {"error": f"Field '{field}' не существует"}

    posts_sorted = sorted(post_db, key=lambda x: getattr(x, field), reverse=descending)
    
    return posts_sorted[:limit]
