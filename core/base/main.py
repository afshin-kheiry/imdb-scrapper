from fastapi import FastAPI

from core.base.auth import router
from core.movies.views import router as movies_router

app = FastAPI()
app.include_router(router)
app.include_router(movies_router)



