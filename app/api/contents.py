from fastapi import FastAPI, APIRouter, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import List

from app.models import Post
from app.config import CLIENT_MAP

app = FastAPI(title="MWS Posts API")
router = APIRouter()


def check_table(table: str):
    """Проверка существования таблицы в CLIENT_MAP"""
    if table not in CLIENT_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Таблица '{table}' не инициализирована. Настройте её через /set-user-data"
        )


# ==================== Базовые эндпоинты ====================

@app.get("/{table}/{post_id}/{field}")
def get_field(post_id: str, field: str, table: str = "general"):
    check_table(table)
    client = CLIENT_MAP[table]

    if field not in Post.model_fields:
        raise HTTPException(400, f"Поле '{field}' не существует в модели Post")

    client.refresh()
    post = client.find_post(post_id)
    if not post:
        raise HTTPException(404, f"Пост с id '{post_id}' не найден")

    return getattr(post, field)


@app.patch("/update/{table}/{post_id}", status_code=status.HTTP_200_OK)
def update_post(
    post_id: str,
    post: Post,                         # теперь просто Post
    table: str = "general"
):
    check_table(table)
    client = CLIENT_MAP[table]

    # Берём только те поля, которые реально передали (остальные будут None)
    fields_to_update = {k: v for k, v in post.dict(exclude_unset=True).items()}

    if not fields_to_update:
        raise HTTPException(400, "Нет полей для обновления")

    data = client.update_record(post_id, fields_to_update)
    return JSONResponse(content={"status": "updated", "record": data})


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_post(
    data: Post,                         # теперь просто Post
    table: str = "general"
):
    check_table(table)
    client = CLIENT_MAP[table]

    record = client.create_record(data.dict())
    client.refresh(force=True)

    return JSONResponse(
        status_code=201,
        content={"status": "created", "record": record}
    )


@router.get("/content")
def get_content(table: str = "general") -> List[Post]:
    check_table(table)
    return CLIENT_MAP[table].get_posts()


@router.get("/sort")
def top_posts(
    field: str,
    limit: int = 10,
    descending: bool = True,
    table: str = "general"
) -> List[Post]:
    check_table(table)
    client = CLIENT_MAP[table]

    if field not in Post.model_fields:
        raise HTTPException(400, f"Поле '{field}' не поддерживается")

    client.refresh()
    return client.sort_posts(field, limit, descending)


@router.get("/filter/{cond}")
def filter_posts(
    cond: str,
    table: str = "general",
    **filters
):
    if cond not in {"eq", "lt", "lte", "gt", "gte"}:
        raise HTTPException(400, "Недопустимое условие фильтра")

    check_table(table)
    return CLIENT_MAP[table].filter_posts(cond, **filters)


# Не забудь включить роутер
app.include_router(router)
