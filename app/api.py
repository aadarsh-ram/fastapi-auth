import os
import pymongo

from fastapi import FastAPI, Body, Depends, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client import OAuthError
from starlette.config import Config

from app.model import PostSchema, UserSchema, UserLoginSchema
from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import signJWT

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", None)
FRONTEND_URL = os.getenv("FRONTEND_URL", None)

if GOOGLE_CLIENT_ID is None or GOOGLE_CLIENT_SECRET is None:
    raise BaseException('Missing env variables')

# Set up OAuth
config_data = {'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID, 'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

# Database setup
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["blog"]
myposts = mydb["posts"] # Blog posts
myusers = mydb["users"] # Login and signup

app = FastAPI()

# Allow anyone to call the API from their own apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

def check_user(data: UserLoginSchema):
    data = myusers.find_one({"email": data.email, "password": data.password})
    if (data):
        return True
    return False

@app.get("/", tags=["root"])
async def read_root() -> dict:
    return {"message": "Welcome to your blog!"}


@app.get("/posts", tags=["posts"])
async def get_posts() -> dict:
    data = list(myposts.find({}, {'_id': 0}))
    return {"data": data}

@app.get("/posts/{id}", tags=["posts"])
async def get_single_post(id: int) -> dict:
    data = list(myposts.find({"id": id}, {'_id': 0}))
    if not len(data):
        return {
            "error": "No such post with the supplied ID."
        }
    return {"data": data}

@app.post("/posts", dependencies=[Depends(JWTBearer())], tags=["posts"])
async def add_post(post: PostSchema) -> dict:
    curr_id = len(list(myposts.find())) + 1
    post.id = curr_id
    myposts.insert_one(post.dict())
    return {
        "data": "Post added!"
    }

@app.route('/google/login')
async def login(request: Request):
    redirect_uri = FRONTEND_URL + '/redirect'  # This creates the url for our /auth endpoint
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.route('/google/token')
async def auth(request: Request):
    try:
        access_token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    user_data = await oauth.google.parse_id_token(request, access_token)
    jwt = signJWT(user_data["email"])
    return jwt

@app.post("/user/signup", tags=["user"])
async def create_user(user: UserSchema = Body(...)):
    myusers.insert_one(user.dict())
    return signJWT(user.email)

@app.post("/user/login", tags=["user"])
async def user_login(user: UserLoginSchema = Body(...)):
    if check_user(user):
        return signJWT(user.email)
    return {
        "error": "Wrong login details!"
    }