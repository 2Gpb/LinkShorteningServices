from fastapi_users import schemas


class UserRead(schemas.BaseUser[int]):
    id: int
    email: str
    username: str

class UserCreate(schemas.BaseUserCreate):
    username: str
    email: str
    password: str