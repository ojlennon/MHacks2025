from fastapi import FastAPI
# from .routers import users, auth

app = FastAPI(title="My FastAPI App")

# app.include_router(users.router)
# app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"message": "Hello World"}