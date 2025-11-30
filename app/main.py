from app.config import VK_TOKEN
from app.parse_vk import parse_vk_posts

posts = parse_vk_posts(VK_TOKEN, 8458649, 2)
print(posts)
