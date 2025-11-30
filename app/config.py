from dotenv import load_dotenv
import os

load_dotenv()

MWS_TOKEN = os.getenv("MTS_API")
VIEW_VK = os.getenv("VIEW_VK")
DST_VK = os.getenv("DST_VK")
OPEN_ROUTER_API = os.getenv("OPEN_ROUTER_API")
VK_TOKEN = os.getenv("VK_TOKEN")


CONFIG_MAP = {
    "mws-token": "",
    "all": [],
    "vk": [],
}

CLIENT_MAP = {}