from fastapi import FastAPI
from contents import router as contents_router

app = FastAPI()
app.include_router(contents_router)
