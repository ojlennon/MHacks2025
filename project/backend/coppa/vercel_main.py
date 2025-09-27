from fastapi import FastAPI
from .vercel_model import get_db

app = FastAPI(title="License Plate Lookup API")

@app.get("/")
def read_root():
    return {"message": "License Plate Lookup API", "version": "1.0.0"}

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

@app.get("/plates")
def list_all_plates():
    """Get all license plates (for testing purposes)"""
    with get_db() as db:
        cursor = db.execute("SELECT * FROM lisence_plates")
        results = cursor.fetchall()
        return {"plates": results, "count": len(results)}
