import os
from cryptography.fernet import Fernet

FERNET = Fernet(os.getenv("ENC_KEY").encode())

CONFIG_MAP = {
    "mws-token": "",
    "all": [],
    "vk": [],
}
CLIENT_MAP = {}