from fastapi import FastAPI, Depends
from fastapi_users import FastAPIUsers
import uvicorn

from auth.models import User
from auth.manager import get_user_manager
from auth.auth import auth_backend
from auth.schemas import UserCreate, UserRead

from links.router import router as links_router
from redirect.router import router as redirect_router


fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend]
)

app = FastAPI()

app.include_router(
    fastapi_users.get_auth_router(auth_backend), 
    prefix='/auth/jwt', 
    tags=['auth']
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate), 
    prefix='/auth', 
    tags=['auth']
)

app.include_router(links_router)
app.include_router(redirect_router)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, host="0.0.0.0", log_level="info")