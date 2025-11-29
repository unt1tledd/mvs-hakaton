import requests
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import List
from app import Post, PostUpdate, PostCreate
from config import *
from .MWSClient import MWSClient

app = FastAPI()
router = APIRouter()

general_client = MWSClient(datasheet_id=DST_ALL, view_id=VIEW_ALL, token=MWS_TOKEN)
vk_client = MWSClient(datasheet_id=DST_VK, view_id=VIEW_VK, token=VK_TOKEN)
tg_client = MWSClient(datasheet_id=DST_TG, view_id=VIEW_TG, token=TG_TOKEN)

CLIENT_MAP = {
    "general": general_client,
    "vk": vk_client,
    "tg": tg_client
}

@app.get("/{post_id}/{field}")
def get_field(post_id: str, field: str, table: str = "general"):
    """
    Возвращает значение указанного поля у поста по ID из выбранной таблицы.

    Args:
        post_id: ID поста
        field: имя поля модели Post для получения значения
        table: ключ таблицы ("general", "vk", "tg")

    Returns:
        Значение указанного поля (str, int или float)

    Raises:
        HTTPException: если пост не найден, поле не существует или таблица неизвестна
    """
    check_table(table)
    
    client = CLIENT_MAP[table]

    client.check_field(field)
    client.refresh()

    post = client.find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail=f"Post with id '{post_id}' not found")

    return getattr(post, field)


@app.patch("/update/{post_id}", status_code=status.HTTP_200_OK)
def update_post(post_id: str, post: PostUpdate, table: str = "general"):
    """
    Обновляет запись поста в MWS Tables по ID в выбранной таблице.

    Args:
        post_id: ID поста
        post: объект PostUpdate с полями для обновления
        table: ключ таблицы ("general", "vk", "tg")

    Returns:
        JSONResponse со структурой:
        {
            "status": "created",
            "record": {...}
        }

    Raises:
        HTTPException: если таблица неизвестна или нет полей для обновления
    """
    check_table(table)
    client = CLIENT_MAP[table]

    fields_to_update = {k: v for k, v in post.dict().items() if v is not None}
    if not fields_to_update:
        raise HTTPException(status_code=400, detail="Нет полей для обновления")

    data = client.update_record(post_id, fields_to_update)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "updated",
            "record": data
        }
    )

@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_post(data: PostCreate, table: str = "general"):
    """
    Создает новую запись в MWS Tables.

    Args:
        data: объект PostCreate, содержащий поля нового поста.
        table: ключ таблицы, в которую нужно сохранить запись.
               Используются таблицы из CLIENT_MAP: "general", "vk", "tg".

    Returns:
        JSONResponse со структурой:
        {
            "status": "created",
            "record": {...}
        }

    Raises:
        HTTPException:
            - если MWS API возвращает ошибку.
            - если таблица некорректная (если проверить заранее).
    """
    
    check_table(table)
    client = CLIENT_MAP[table]

    created_record = client.create_record(data.dict())
    client.refresh(force=True)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "status": "created",
            "record": created_record
        }
    )


@router.get("/content")
def get_content(table: str = "general") -> List[Post]:
    """
    Возвращает список всех постов из выбранной таблицы.

    Args:
        table: ключ таблицы ("general", "vk", "tg")

    Returns:
        Список объектов Post

    Raises:
        HTTPException: если таблица неизвестна
    """
    check_table(table)
    client = CLIENT_MAP[table]

    return client.get_posts()


@router.get("/sort_post")
def top_posts(field: str, limit: int = 10, descending: bool = True, table: str = "general") -> List[Post]:
    """
    Возвращает топ постов по указанному полю из выбранной таблицы.

    Args:
        field: поле модели Post для сортировки (например, views, likes)
        limit: количество возвращаемых записей (по умолчанию 10)
        descending: сортировка по убыванию (по умолчанию True)
        table: ключ таблицы ("general", "vk", "tg")

    Returns:
        Список объектов Post, отсортированных по указанному полю
    """
    check_table(table)
    client = CLIENT_MAP[table]

    client.check_field(field)
    client.refresh()
    return client.sort_posts(field, limit, descending)


@router.get("/filter/{cond}")
def filter_posts(cond: str, table: str = "general", **filters):
    """
    Фильтрует посты по условию cond (eq, lt, lte, gt, gte) из выбранной таблицы.

    Args:
        cond: условие фильтрации ("eq", "lt", "lte", "gt", "gte")
        table: ключ таблицы ("general", "vk", "tg")
        filters: словарь фильтров field=value

    Returns:
        Список объектов Post, удовлетворяющих условию
    """
    check_table(table)
    client = CLIENT_MAP[table]

    return client.filter_posts(cond, **filters)

def check_table(table: str):
    if table not in CLIENT_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown table: {table}")

app.include_router(router)