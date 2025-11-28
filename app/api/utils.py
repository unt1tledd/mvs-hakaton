import requests
from config import TOKEN
from app import Post

post_db: list[Post] = []

def get_mws_posts():
    """ Получает все записи из MWS Tables """

    url = "https://tables.mws.ru/fusion/v1/datasheets/dstN41eFMNhEyEi7BJ/records"

    params = {
        "viewId": "viwCG9BUCxf1C",
        "fieldKey": "name"
    }

    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    global post_db
    post_db = [Post(**item) for item in data["records"]]
    
    return post_db

def find_post(id: str) -> Post | None:
    """ Ищет пост в локальном кешe post_db """

    for post in post_db:
        if post.id == id:
            return post
    return None
