from app.config import MWS_TOKEN
from app.parse_vk import parse_vk_posts

posts = parse_vk_posts(MWS_TOKEN, 8458649, 2)
