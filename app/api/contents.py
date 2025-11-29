import requests
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
from app.models import VKPost
from app.parse_vk import parse_vk_posts
from config import *
from .MWSClient import MWSClient
import io
import json

app = FastAPI(title="VK Content Analytics API")
router = APIRouter()

# CORS для связи фронтенда и бэкенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене замените на конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели для новых endpoints
class ConfigData(BaseModel):
    api_mws: str
    url_tables: str = ""
    api_vk: str
    id_group: str
    count: int = 10

class ParseVKRequest(BaseModel):
    api_key: str
    group_id: int
    count: int = 10

vk_client = MWSClient(datasheet_id=DST_VK, view_id=VIEW_VK, token=MWS_TOKEN, model=VKPost)

@app.get("/{post_id}/{field}")
def get_field(post_id: str, field: str):
    """
    Возвращает значение указанного поля у поста по ID из VK.

    Args:
        post_id: ID поста
        field: имя поля модели VKPost для получения значения

    Returns:
        Значение указанного поля (str, int или float)

    Raises:
        HTTPException: если пост не найден или поле не существует
    """
    vk_client.check_field(field)
    vk_client.refresh()

    post = vk_client.find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail=f"Post with id '{post_id}' not found")

    return getattr(post, field)


@app.patch("/update/{post_id}", status_code=status.HTTP_200_OK)
def update_post(post_id: str, fields: dict):
    """
    Обновляет запись поста в MWS Tables по ID.

    Args:
        post_id: ID поста
        fields: словарь с полями для обновления

    Returns:
        JSONResponse со структурой:
        {
            "status": "updated",
            "record": {...}
        }

    Raises:
        HTTPException: если нет полей для обновления
    """
    if not fields:
        raise HTTPException(status_code=400, detail="Нет полей для обновления")

    data = vk_client.update_record(post_id, fields)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "updated",
            "record": data
        }
    )

@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_post(data: VKPost):
    """
    Создает новую запись в MWS Tables.

    Args:
        data: объект VKPost, содержащий поля нового поста.

    Returns:
        JSONResponse со структурой:
        {
            "status": "created",
            "record": {...}
        }

    Raises:
        HTTPException: если MWS API возвращает ошибку.
    """
    created_record = vk_client.create_record(data.dict())
    vk_client.refresh(force=True)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "status": "created",
            "record": created_record
        }
    )


@router.get("/content")
def get_content() -> List[VKPost]:
    """
    Возвращает список всех постов из VK.

    Returns:
        Список объектов VKPost
    """
    return vk_client.get_posts()


@router.get("/sort_post")
def top_posts(field: str, limit: int = 10, descending: bool = True) -> List[VKPost]:
    """
    Возвращает топ постов по указанному полю из VK.

    Args:
        field: поле модели VKPost для сортировки (например, views, likes)
        limit: количество возвращаемых записей (по умолчанию 10)
        descending: сортировка по убыванию (по умолчанию True)

    Returns:
        Список объектов VKPost, отсортированных по указанному полю
    """
    vk_client.check_field(field)
    vk_client.refresh()
    return vk_client.sort_posts(field, limit, descending)


@router.get("/filter/{cond}")
def filter_posts(cond: str, **filters) -> List[VKPost]:
    """
    Фильтрует посты по условию cond (eq, lt, lte, gt, gte) из VK.

    Args:
        cond: условие фильтрации ("eq", "lt", "lte", "gt", "gte")
        filters: словарь фильтров field=value

    Returns:
        Список объектов VKPost, удовлетворяющих условию
    """
    return vk_client.filter_posts(cond, **filters)


# ========== Новые endpoints для фронтенда ==========

@router.get("/api/download-template")
def download_template():
    """
    Скачивает CSV шаблон для MWS Tables.

    Returns:
        CSV файл с шаблоном
    """
    # Создаем CSV шаблон
    csv_content = """post_id,platform,format,date,likes,shares,comment_count,views,owner_id,reposts,polls_participation
123,VK,photo,2025-01-01,100,50,20,1000,-12345,10,0
124,VK,video,2025-01-02,200,80,35,2500,-12345,25,0
"""

    # Возвращаем как файл для скачивания
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=template.csv"}
    )


@router.post("/api/save-config")
def save_config(config: ConfigData):
    """
    Сохраняет конфигурацию пользователя (API ключи, настройки).

    Args:
        config: объект конфигурации

    Returns:
        Статус сохранения
    """
    # TODO: Сохранить конфигурацию в БД или файл
    # Пока просто возвращаем успех
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "message": "Конфигурация сохранена",
            "config": config.dict()
        }
    )


@router.post("/api/parse-vk")
def parse_vk_endpoint(request: ParseVKRequest):
    """
    Парсит посты из VK и сохраняет в MWS Tables.

    Args:
        request: параметры парсинга (api_key, group_id, count)

    Returns:
        Список распарсенных постов
    """
    try:
        # Парсим VK
        posts = parse_vk_posts(request.api_key, request.group_id, request.count)

        # Сохраняем в MWS Tables
        created_records = []
        for post in posts:
            try:
                record = vk_client.create_record(post.dict())
                created_records.append(record)
            except Exception as e:
                print(f"Ошибка сохранения поста {post.post_id}: {e}")
                continue

        vk_client.refresh(force=True)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": f"Распарсено {len(posts)} постов, сохранено {len(created_records)}",
                "posts_count": len(posts),
                "saved_count": len(created_records)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка парсинга VK: {str(e)}"
        )


@router.get("/api/export/{format}")
def export_data(format: str):
    """
    Экспортирует данные в указанном формате.

    Args:
        format: формат экспорта (csv, json)

    Returns:
        Файл с данными
    """
    posts = vk_client.get_posts()

    if format == "csv":
        # Экспорт в CSV
        csv_lines = ["post_id,platform,format,date,likes,shares,comment_count,views,owner_id,reposts"]
        for post in posts:
            csv_lines.append(
                f"{post.post_id},{post.platform},{post.format},{post.date},"
                f"{post.likes},{post.shares},{post.comment_count},{post.views},"
                f"{post.owner_id},{post.reposts}"
            )
        csv_content = "\n".join(csv_lines)

        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=export.csv"}
        )

    elif format == "json":
        # Экспорт в JSON
        posts_dict = [post.dict() for post in posts]
        json_content = json.dumps(posts_dict, indent=2, default=str, ensure_ascii=False)

        return StreamingResponse(
            io.StringIO(json_content),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=export.json"}
        )

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат: {format}. Используйте 'csv' или 'json'"
        )


@router.get("/api/statistics")
def get_statistics():
    """
    Возвращает агрегированную статистику по всем постам.

    Returns:
        Объект со статистикой
    """
    posts = vk_client.get_posts()

    if not posts:
        return {
            "total_posts": 0,
            "total_views": 0,
            "total_likes": 0,
            "total_comments": 0,
            "total_reposts": 0,
            "avg_views": 0,
            "avg_likes": 0,
            "avg_comments": 0
        }

    total_views = sum(post.views for post in posts)
    total_likes = sum(post.likes for post in posts)
    total_comments = sum(post.comment_count for post in posts)
    total_reposts = sum(post.reposts for post in posts)

    return {
        "total_posts": len(posts),
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_reposts": total_reposts,
        "avg_views": total_views / len(posts),
        "avg_likes": total_likes / len(posts),
        "avg_comments": total_comments / len(posts)
    }


app.include_router(router)