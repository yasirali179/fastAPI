# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from cachetools import TTLCache
from urllib.parse import quote_plus

# Initialize FastAPI app
app = FastAPI()

# Dependency for database
DATABASE_URL = "mysql+mysqlconnector://username:%s@localhost/db" % quote_plus("password")
engine = create_engine(DATABASE_URL)
SessionLocal = scoped_session(sessionmaker(bind=engine))
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for OAuth2 password bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency for caching
cache = TTLCache(maxsize=1000, ttl=300)

# SQLAlchemy model for User
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(100))

# Create tables
metadata = MetaData()
Base.metadata.create_all(bind=engine)

# Pydantic model for Signup
class Signup(BaseModel):
    email: str
    password: str

# Pydantic model for Login
class Login(BaseModel):
    email: str
    password: str

# Pydantic model for AddPost
class AddPost(BaseModel):
    text: str

# Pydantic model for DeletePost
class DeletePost(BaseModel):
    postID: str

# Function to get the current user based on the token
def get_current_user(token: str = Depends(oauth2_scheme)):
    # You would usually decode and verify the token here
    # For simplicity, we are using a dummy implementation
    if token != "dummytoken":
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

# Endpoint for signup
@app.post("/signup")
def signup(signup: Signup):
    # Create user in the database (skipping password hashing for simplicity)
    # You should use a proper password hashing library in a real-world scenario
    user = User(email=signup.email, password=signup.password)
    SessionLocal.add(user)
    SessionLocal.commit()

    # Dummy token generation (should use JWT or OAuth2 in a real-world scenario)
    token = "dummytoken"
    return {"token": token}

# Endpoint for login
@app.post("/login")
def login(login: Login):
    # Check user credentials in the database (skipping password hashing for simplicity)
    # You should use a proper password hashing library in a real-world scenario
    user = SessionLocal.query(User).filter(User.email == login.email).first()
    if user and user.password == login.password:
        # Dummy token generation (should use JWT or OAuth2 in a real-world scenario)
        token = "dummytoken"
        return {"token": token}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Endpoint for adding a post
@app.post("/addPost")
def add_post(post: AddPost, current_user: str = Depends(get_current_user)):
    # Check payload size
    if len(post.text) > 1024 * 1024:  # 1 MB limit
        raise HTTPException(status_code=400, detail="Payload size too large")

    # Save post in memory (dummy implementation)
    post_id = hash(post.text)  # Use a proper post ID generation method in a real-world scenario

    # Dummy caching of post_id
    cache[post_id] = post.text

    return {"postID": str(post_id)}

# Endpoint for getting posts
@app.get("/getPosts")
def get_posts(current_user: str = Depends(get_current_user)):
    # Dummy implementation to fetch posts from cache
    user_posts = list(cache.values())
    return {"posts": user_posts}

# Endpoint for deleting a post
@app.post("/deletePost")
def delete_post(delete_post: DeletePost, current_user: str = Depends(get_current_user)):
    # Dummy implementation to delete post from cache
    post_id = delete_post.postID
    if post_id in cache:
        del cache[post_id]
        return {"message": "Post deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Post not found")

# Additional FastAPI settings for response caching
@app.middleware("http")
async def cache_middleware(request, call_next):
    response = await call_next(request)
    if request.method == "GET" and request.url.path == "/getPosts" and response.status_code == 200:
        response.headers["Cache-Control"] = "public, max-age=300"  # Cache for 5 minutes
    return response
