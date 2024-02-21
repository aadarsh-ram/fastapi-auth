from fastapi import FastAPI, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
import pymongo

from app.model import PostSchema, UserSchema, UserLoginSchema
from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import signJWT

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