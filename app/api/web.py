import os
from fastapi import FastAPI, APIRouter, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.config import FERNET, CONFIG_MAP, CLIENT_MAP

from app.models import Post, VKPost
from app.api.mws_client import MWSClient

app = FastAPI(title="MWS Analytics")
router = APIRouter()

templates = Jinja2Templates(directory="frontend")

MODEL = {
    "all": Post,
    "vk": VKPost,
}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== ВСПОМОГАТЕЛЬНЫЕ ======================
class DummyClient:
    def get_posts(self): return []
    def refresh(self, force=False): pass

DUMMY = DummyClient()

def save_platform_config(platform: str, dst_id: str, view_id: str, token: str, group_id: str = ""):
    """Сохраняет конфиг платформы в CONFIG_MAP и создаёт клиент"""
    encrypted_token = FERNET.encrypt(token.encode()).decode()

    config_entry = {
        "dstId": dst_id,
        "viewId": view_id,
        "token": encrypted_token,
        "id": group_id or "unknown"
    }

    # Убираем дубли
    CONFIG_MAP["all"] = [c for c in CONFIG_MAP["all"] if c.get("dstId") != dst_id]
    if platform not in CONFIG_MAP:
        CONFIG_MAP[platform] = []
    CONFIG_MAP[platform] = [c for c in CONFIG_MAP[platform] if c.get("dstId") != dst_id]
    CONFIG_MAP[platform].append(config_entry)
    CONFIG_MAP["all"].append(config_entry)

    # Создаём клиент
    try:
        client = MWSClient(
            datasheet_id=dst_id,
            view_id=view_id,
            token=token,
            model=MODEL["platform"]
        )
        client.refresh(force=True)
        CLIENT_MAP[f"{platform}_{dst_id}"] = client
    except Exception as e:
        print(f"[ERROR] Не удалось создать клиент для {platform}: {e}")
        CLIENT_MAP[f"{platform}_{dst_id}"] = DUMMY

# ====================== ОСНОВНЫЕ ЭНДПОИНТЫ ======================
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Сохранение основного токена
@router.post("/mws-api")
async def save_main_token(payload: dict):
    token = payload.get("mws-token")
    if not token:
        raise HTTPException(400, "Токен не передан")
    CONFIG_MAP["mws-token"] = FERNET.encrypt(token.encode()).decode()
    return {"status": "ok"}

# Добавление таблицы — основной эндпоинт для фронта
@router.post("/api/add-table")
async def add_table(
    table_name: str = Form("vk_main"),
    platform: str = Form("vk"),
    url: str = Form(""),
    token: str = Form(""),
    group_id: str = Form("")
):
    if not url or not token:
        raise HTTPException(400, "URL и токен обязательны")

    try:
        parts = url.strip("/").split("/")
        dst_id = parts[parts.index("datasheets") + 1]
        view_id = parts[parts.index("views") + 1] if "views" in parts else parts[-1]
    except Exception:
        raise HTTPException(400, "Неверная ссылка на таблицу MWS")

    save_platform_config(platform, dst_id, view_id, token, group_id)

    return {
        "status": "success",
        "table": table_name,
        "platform": platform,
        "records": len(CLIENT_MAP.get(f"{platform}_{dst_id}", DUMMY).get_posts())
    }

# Статистика
@router.get("/api/statistics")
async def get_statistics():
    all_posts = []
    for client in CLIENT_MAP.values():
        try:
            all_posts.extend(client.get_posts())
        except:
            continue

    if not all_posts:
        return {"total_posts": 0, "total_views": 0, "total_likes": 0, "total_comments": 0}

    views = sum(getattr(p, "views", 0) for p in all_posts)
    likes = sum(getattr(p, "likes", 0) for p in all_posts)
    comments = sum(getattr(p, "comment_count", 0) for p in all_posts)

    total = len(all_posts)
    return {
        "total_posts": total,
        "total_views": views,
        "total_likes": likes,
        "total_comments": comments,
        "avg_views": round(views / total, 1) if total else 0,
        "avg_likes": round(likes / total, 1) if total else 0,
    }

# Графики — заглушки (можно потом сделать реальные)
@router.get("/chart-data")
async def chart_data(metric: str = "likes", period: str = "week"):
    data = {
        "likes": [120, 280, 190, 420, 380, 610, 520],
        "views": [2100, 3200, 2800, 4900, 4300, 7200, 6800]
    }
    return {
        "labels": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
        "values": data.get(metric, data["likes"])
    }

@router.get("/chart-reach")
async def chart_reach():
    return {
        "labels": ["Органика", "Реклама", "Репосты"],
        "values": [65, 25, 10]
    }
@router.get("/api/download-template/{platform}")
async def download_template(platform: str):
    """
    Скачивание шаблона:
    - /api/download-template/vk     → vk.xlsx
    - /api/download-template/all    → all.xlsx
    - любой другой                  → all.xlsx (по умолчанию)
    """

    platform = platform.lower().strip()

    if platform == "vk":
        filename = "vk.xlsx"
    else:
        filename = "all.xlsx"

    file_path = os.path.join("templatemplates_xlsxtes", filename)

    # Проверка, что файл существует (на всякий случай)
    if not os.path.exists(file_path):
        # Если нет — отдаём all.xlsx как fallback
        file_path = os.path.join("templates_xlsx", "all.xlsx")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

app.include_router(router)  # если нужны и без /api