import requests
from datetime import datetime
from typing import List
from models import VKPost

def parse_vk_posts(api_key: str, group_id: int, count: int = 10) -> List[VKPost]:
    """Получает посты из VK и преобразует в VKPost модели"""

    params = {
        "owner_id": -group_id,
        "count": count,
        "access_token": api_key,
        "v": "5.131"
    }

    response = requests.get("https://api.vk.com/method/wall.get", params=params)
    data = response.json()
    posts_raw = data['response']['items']

    vk_posts: List[VKPost] = []

    for post in posts_raw:
        content_format = 'text'
        if post.get('attachments'):
            content_format = post['attachments'][0]['type']

        vk_post = VKPost(
            post_id=post['id'],
            owner_id=post['owner_id'],
            platform='VK',
            format=content_format,
            date=datetime.fromtimestamp(post['date']),
            likes=post['likes']['count'],
            comment_count=post['comments']['count'],
            views=post['views']['count'],
            reposts=post.get('reposts', {}).get('count', 0),
            shares=0
        )

        vk_posts.append(vk_post)

    return vk_posts