from fastapi import FastAPI
import uvicorn

from core.redis import lifespan
from auth.router import router as auth_router
from links.router import router as links_router
from links.redirect_router import router as redirect_router


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(links_router)
app.include_router(redirect_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        reload=True, 
        host="0.0.0.0", 
        log_level="info"
    )
