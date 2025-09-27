from fastapi import FastAPI
from .model import get_db

# from .routers import users, auth

app = FastAPI(title="My FastAPI App")

# app.include_router(users.router)
# app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/plates/{plate_number}")
def read_plate(plate_number: str):
    with get_db() as db:
        cursor = db.execute(
            "SELECT * FROM lisence_plates WHERE plate_number = ?", 
            (plate_number,)
        )
        result = cursor.fetchone()
        
        if result is None:
            return {"error": "Plate number not found"}
        
        return result