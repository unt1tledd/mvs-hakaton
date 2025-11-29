from dotenv import load_dotenv
import os

load_dotenv()

MWS_TOKEN = os.getenv("MTS_API")
VIEW_ALL = os.getenv("VIEW_ALL")
DST_ALL = os.getenv("DST_VK")

VK_TOKEN = os.getenv("VK_TOKEN")
VIEW_VK = os.getenv("VIEW_VK")
DST_VK = os.getenv("DST_VK")

TG_TOKEN = os.getenv("TG_TOKEN")
VIEW_TG = os.getenv("VIEW_TG")
DST_TG = os.getenv("DST_TG")

YANDEX_METRIKA_TOKEN = os.getenv("YANDEX_METRIKA_TOKEN")
VIEW_YANDEX_METRIKA = os.getenv("VIEW_YANDEX_METRIKA")