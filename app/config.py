from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("MTS_API")
if not TOKEN:
    raise RuntimeError("Add token")
