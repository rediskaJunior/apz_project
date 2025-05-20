import os
import sys
import uuid
import json
import argparse
import hazelcast
import secrets
import uvicorn
import datetime
import bcrypt
from typing import Dict, Optional
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.consul_utils import register_service, deregister_service, get_consul_kv


class User(BaseModel):
    login: str
    password: str

#to store user info in the db - login and hashed password
class UserInDB(BaseModel):
    login: str
    hashed_password: str
    user_id: str

class Token(BaseModel):
    token: str
    token_type: str

class TokenData(BaseModel):
    login: Optional[str] = None
    user_id: Optional[str] = None

SECRET_KEY = secrets.token_hex(32)  # Секретний ключ для JWT
ALGORITHM = "HS256"  # Алгоритм для JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Час життя токена (24 години)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

class AuthService:
    def __init__(self, cluster_name, queue_name, map_name, service_name="auth-service"):
        self.hz_client = hazelcast.HazelcastClient(cluster_name=cluster_name)
        self.users_map = self.hz_client.get_map(map_name).blocking()
        self.service_name = service_name
        self.msg_queue = self.hz_client.get_queue(queue_name)
        self.service_id = f"{service_name}-{os.getpid()}"
    

    #To create a jwt access token
    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    #To verify if entered password is correct
    def verify_password(self, plain_password, hashed_password):
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    #To hash the password
    def get_password_hash(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    #To check if the user is in the db and return user data
    def get_user(self, login: str):
        user_data = self.users_map.get(login)
        if user_data:
            user_dict = json.loads(user_data)
            return UserInDB(**user_dict)
        return None
    
    #to login existing user
    def authenticate_user(self, login: str, password: str):
        user = self.get_user(login)
        if not user:
            return False
        if not self.verify_password(password, user.hashed_password):
            return False
        return user


    #to register a new user
    def register_user(self, user: User):
        if self.get_user(user.login):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Користувач з таким логіном вже існує"
            )
        user_id = str(uuid.uuid4())
        hashed_password = self.get_password_hash(user.password)
        user_in_db = UserInDB(login=user.login, hashed_password=hashed_password, user_id=user_id)
        self.users_map.put(user.login, json.dumps(user_in_db.dict()))
        return {"login": user.login, "user_id": user_id}

    async def get_current_user(self, token: str = Depends(oauth2_scheme)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не вдалося підтвердити облікові дані",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            login: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            if login is None or user_id is None:
                raise credentials_exception
            token_data = TokenData(login=login, user_id=user_id)
        except JWTError:
            raise credentials_exception
        user = self.get_user(token_data.login)
        if user is None:
            raise credentials_exception
        return user    

    def shutdown(self):
        self.hz_client.shutdown()
        print("Hazelcast client shutdown")

app = FastAPI()
auth_service = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or replace "*" with the frontend's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------- DEFAULT ENDPOINTS ---------------

@app.on_event("startup")
async def startup_event():
    global auth_service
    cluster_name_ = await get_consul_kv("cluster-name")
    queue_name_ = await get_consul_kv("queue-name")
    map_name_ = await get_consul_kv("auth-map")
    auth_service = AuthService(cluster_name=cluster_name_, queue_name = queue_name_, map_name=map_name_, service_name="auth-service")
    
    port = int(os.environ["APP_PORT"])
    await register_service(auth_service.service_name, auth_service.service_id, "localhost", port)


@app.on_event("shutdown")
async def shutdown():
    await deregister_service(auth_service.service_id)
    auth_service.shutdown()
    print("Auth Service shutdown")


@app.get("/health")
async def health_check():
    return {"status": "OK"}

# -------------- AUTHENTIFICATION ENDPOINTS ---------------

@app.post("/auth/register", response_model=Dict)
async def register(user: User):
    return auth_service.register_user(user)

@app.post("/auth/login", response_model=Token)
async def login(user: User):
    db_user = auth_service.authenticate_user(user.login, user.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірний логін або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(
        data={"sub": db_user.login, "user_id": db_user.user_id}
    )
    return {"token": access_token, "token_type": "bearer"}

# -------------- STARTUP ---------------

if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8591)
    args = parser.parse_args()

    os.environ["APP_PORT"] = str(args.port)

    uvicorn.run("auth_service:app", host="0.0.0.0", port=args.port, reload=False)