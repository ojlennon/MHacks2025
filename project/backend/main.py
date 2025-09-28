import base64
import imghdr
import os
import re
from typing import Optional, List, Dict
from datetime import date, datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI(title="Plate OCR")

# Get OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

client = OpenAI(api_key=OPENAI_API_KEY)
PLATE_EXTRACTION_PROMPT = """
Analyze this image of a license plate and extract ONLY the license plate number.
Rules:
- Return only the alphanumeric characters on the plate
- Remove any spaces, dashes, or special characters
- If multiple plates are visible, return the most prominent one
- If no license plate is clearly visible, return "NONE"
- Maximum 10 characters
- Return just the plate number, nothing else
"""
CLEAN_RE = re.compile(r"[^A-Z0-9 ]+")

# License Plate Data Models
class LicensePlate(BaseModel):
    plate_number: str
    owner_name: str
    dob: date
    has_warrant: bool
    warrant_reason: Optional[str]
    registration_date: date
    is_stolen: bool

# In-memory database
license_plates_db: Dict[str, LicensePlate] = {
    'ABC1234': LicensePlate(
        plate_number='ABC1234',
        owner_name='John Doe',
        dob=date(1985, 6, 15),
        has_warrant=False,
        warrant_reason=None,
        registration_date=date(2020, 1, 10),
        is_stolen=False
    ),
    'XYZ789': LicensePlate(
        plate_number='XYZ789',
        owner_name='Jane Smith',
        dob=date(1990, 11, 22),
        has_warrant=True,
        warrant_reason='Unpaid parking tickets',
        registration_date=date(2019, 3, 5),
        is_stolen=False
    ),
    'LMN456': LicensePlate(
        plate_number='LMN456',
        owner_name='Alice Johnson',
        dob=date(1978, 2, 28),
        has_warrant=False,
        warrant_reason=None,
        registration_date=date(2021, 7, 19),
        is_stolen=True
    ),
    'DEF321': LicensePlate(
        plate_number='DEF321',
        owner_name='Bob Brown',
        dob=date(2000, 12, 12),
        has_warrant=True,
        warrant_reason='Speeding violations',
        registration_date=date(2018, 9, 30),
        is_stolen=False
    )
}




class ExtractResponse(BaseModel):
    plate: str

class Base64ImageRequest(BaseModel):
    base64_image: str

class LicensePlateResponse(BaseModel):
    plate_number: str
    owner_name: str
    dob: date
    has_warrant: bool
    warrant_reason: Optional[str]
    registration_date: date
    is_stolen: bool

class PlateSearchResult(BaseModel):
    found: bool
    data: Optional[LicensePlateResponse] = None
    alerts: List[str] = []

# Utility functions for license plate operations
def lookup_plate(plate_number: str) -> Optional[LicensePlate]:
    """Look up a license plate in the in-memory database"""
    return license_plates_db.get(plate_number.upper())

def add_plate(plate_data: LicensePlate) -> bool:
    """Add a new license plate to the database"""
    license_plates_db[plate_data.plate_number.upper()] = plate_data
    return True

def remove_plate(plate_number: str) -> bool:
    """Remove a license plate from the database"""
    plate_key = plate_number.upper()
    if plate_key in license_plates_db:
        del license_plates_db[plate_key]
        return True
    return False

def get_all_plates() -> List[LicensePlate]:
    """Get all license plates from the database"""
    return list(license_plates_db.values())

def search_plates_with_alerts(plate_number: str) -> PlateSearchResult:
    """Search for a plate and return any alerts"""
    plate = lookup_plate(plate_number)
    if not plate:
        return PlateSearchResult(found=False)
    
    alerts = []
    if plate.has_warrant:
        alerts.append(f"WARRANT: {plate.warrant_reason}")
    if plate.is_stolen:
        alerts.append("STOLEN VEHICLE")
    
    return PlateSearchResult(
        found=True,
        data=LicensePlateResponse(**plate.model_dump()),
        alerts=alerts
    )

def todata_url(image_bytes: bytes) -> str:
    # Try to guess the image type (fallback to png)
    kind = imghdr.what(None, h=image_bytes) or "png"
    b64 = base64.b64encode(image_bytes).decode("ascii")
    return f"data:image/{kind};base64,{b64}"

def askopenai(image_ref: str) -> str:
    """
    Call OpenAI with a single instruction + one image.
    image_ref: either http(s) URL or a data: URL (base64).
    """
    # Prompt keeps it deterministic and asks for only the plate text.
    prompt = (
        "Extract ONLY the license plate text (letters/numbers/spaces). "
        "No extra words, no state names. If nothing is legible, reply with 'UNKNOWN'."
        "If there is a dash in the plate, ommit the dash. "
        "If this is not a license plate, reply with 'UNKNOWN'."
    )
    
    # Responses API with a vision model
    # (Images may be passed via URL or Base64 data URL.)
    resp = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": image_ref, "detail": "low"},
                ],
            }
        ],
        temperature=0,
        max_output_tokens=32,
    )
    
    # SDK exposes a convenience string:
    # (If unavailable in your SDK version, fall back to parsing the first text item.)
    text = getattr(resp, "output_text", None)
    if not text:
        # fallback parser
        try:
            parts = resp.output[0].content # type: ignore[attr-defined]
            text = "".join(p.text for p in parts if getattr(p, "type", "") == "output_text")
        except Exception:
            text = ""
    
    text = text.strip().upper()
    # Keep only plate-ish characters
    text = CLEAN_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or "UNKNOWN"

import json
import re
from typing import List

def askopenai_list(image_ref: str) -> List[str]:
    """
    Call OpenAI with a single instruction + one image.
    image_ref: either http(s) URL or a data: URL (base64).
    """
    prompt = (
        "You are receiving an image that may contain multiple license plates. "
        "Extract ONLY the license plate texts (letters/numbers/spaces). "
        "No extra words, no state names. If nothing is legible, reply with 'UNKNOWN'."
        "If there is a dash in the plate, ommit the dash. "
        "If this is not a license plate, reply with 'UNKNOWN'."
        "Return the results as an array of strings, e.g. [\"ABC123\", \"XYZ789\"]"
    )
    
    resp = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": image_ref, "detail": "low"},
                ],
            }
        ],
        temperature=0,
        max_output_tokens=32,
    )
    
    text = getattr(resp, "output_text", None)
    if not text:
        try:
            parts = resp.output[0].content
            text = "".join(p.text for p in parts if getattr(p, "type", "") == "output_text")
        except Exception:
            text = ""
    
    text = text.strip()
    
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return [str(item).upper().replace("-", "").strip() for item in result if str(item).strip()]
        else:
            return [str(result).upper().replace("-", "").strip()]
    except json.JSONDecodeError:
        if text.upper() == "UNKNOWN" or not text:
            return ["UNKNOWN"]
        return [text.upper().replace("-", "").strip()]

@app.post("/extract", response_model=ExtractResponse)
async def extract_plate(
    image_url: Optional[str] = Query(default=None, description="HTTP URL of the image"),
    file: Optional[UploadFile] = File(default=None, description="Image file upload"),
    base64_image: Optional[str] = Query(default=None, description="Base64 encoded image string"),
):
    # Check that exactly one input method is provided
    input_methods = [image_url, file, base64_image]
    provided_methods = [method for method in input_methods if method is not None]
    
    if len(provided_methods) == 0:
        raise HTTPException(status_code=400, detail="Provide either image_url, file, or base64_image.")
    
    if len(provided_methods) > 1:
        raise HTTPException(status_code=400, detail="Provide only one input method: image_url, file, or base64_image.")
    
    
    try:
        if image_url:
            image_ref = image_url
        elif base64_image:
            # Handle base64 string
            try:
                # Clean up the base64 string first
                base64_clean = base64_image.strip()
                
                # Check if it's already a data URL
                if base64_clean.startswith('data:image/'):
                    image_ref = base64_clean
                else:
                    # Remove any URL encoding artifacts
                    import urllib.parse
                    base64_clean = urllib.parse.unquote(base64_clean)
                    
                    # Remove any whitespace or newlines that might have been added
                    base64_clean = ''.join(base64_clean.split())
                    
                    # Try to decode to validate it's valid base64
                    try:
                        decoded_data = base64.b64decode(base64_clean, validate=True)
                    except Exception:
                        raise HTTPException(status_code=400, detail="Invalid base64 encoding")
                    
                    # Check if decoded data is actually an image
                    if len(decoded_data) < 100:  # Too small to be a real image
                        raise HTTPException(status_code=400, detail="Base64 data too small to be a valid image")
                    
                    # Detect image type from the actual data
                    image_type = imghdr.what(None, h=decoded_data)
                    if not image_type:
                        # Try common image signatures
                        if decoded_data.startswith(b'\xFF\xD8\xFF'):
                            image_type = 'jpeg'
                        elif decoded_data.startswith(b'\x89PNG\r\n\x1a\n'):
                            image_type = 'png'
                        elif decoded_data.startswith(b'GIF87a') or decoded_data.startswith(b'GIF89a'):
                            image_type = 'gif'
                        else:
                            image_type = 'jpeg'  # Default fallback
                    
                    # Create proper data URL
                    image_ref = f"data:image/{image_type};base64,{base64_clean}"
                    
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {e}")
        else:
            # Handle file upload
            data = await file.read()
            if not data:
                raise HTTPException(status_code=400, detail="Empty file.")
            image_ref = todata_url(data)
        
        plate = askopenai(image_ref).replace(" ", "")
        
        plate_info = lookup_plate(plate)
        if plate_info:
            return JSONResponse(status_code=200, content={
                "plate": plate,
                "owner_name": plate_info.owner_name,
                "dob": plate_info.dob.isoformat(),
                "has_warrant": plate_info.has_warrant,
                "warrant_reason": plate_info.warrant_reason,
                "registration_date": plate_info.registration_date.isoformat(),
                "is_stolen": plate_info.is_stolen
            })
        else:
            fake_data = {
            "plate": "TJX 9717",
            "owner_name": "Matias Pena",
            "dob": "01/13/2004",
            "has_warrant": True,
            "registration_date": "09/28/2025",
            "license_ex_date": "12/31/2025",
            "warrant_reason": "Hello!",
            "is_stolen": True
          }
            # return JSONResponse(status_code=404, content={"detail": f"License plate {plate} not found"})
            return JSONResponse(status_code=203, content=fake_data)
        # return JSONResponse(status_code=200, content=ExtractResponse(plate=plate).model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {e}")

@app.post("/extract-base64", response_model=ExtractResponse)
async def extract_plate_base64(request: Base64ImageRequest):
    """Extract license plate from base64 image data (sent in request body)"""
    try:
        base64_image = request.base64_image.strip()
        
        # Handle base64 string
        try:
            # Check if it's already a data URL
            if base64_image.startswith('data:image/'):
                image_ref = base64_image
            else:
                # Remove any URL encoding artifacts
                import urllib.parse
                base64_clean = urllib.parse.unquote(base64_image)
                
                # Remove any whitespace or newlines
                base64_clean = ''.join(base64_clean.split())
                
                # Try to decode to validate it's valid base64
                try:
                    decoded_data = base64.b64decode(base64_clean, validate=True)
                except Exception:
                    raise HTTPException(status_code=400, detail="Invalid base64 encoding")
                
                # Check if decoded data is actually an image
                if len(decoded_data) < 100:
                    raise HTTPException(status_code=400, detail="Base64 data too small to be a valid image")
                
                # Detect image type from the actual data
                image_type = imghdr.what(None, h=decoded_data)
                if not image_type:
                    # Try common image signatures
                    if decoded_data.startswith(b'\xFF\xD8\xFF'):
                        image_type = 'jpeg'
                    elif decoded_data.startswith(b'\x89PNG\r\n\x1a\n'):
                        image_type = 'png'
                    elif decoded_data.startswith(b'GIF87a') or decoded_data.startswith(b'GIF89a'):
                        image_type = 'gif'
                    else:
                        image_type = 'jpeg'  # Default fallback
                
                # Create proper data URL
                image_ref = f"data:image/{image_type};base64,{base64_clean}"
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {e}")
        
        # Process the image
        plate = askopenai(image_ref).replace(" ", "")
        
        # Look up plate info
        plate_info = lookup_plate(plate)
        if plate_info:
            return JSONResponse(status_code=200, content={
                "plate": plate,
                "owner_name": plate_info.owner_name,
                "dob": plate_info.dob.isoformat(),
                "has_warrant": plate_info.has_warrant,
                "warrant_reason": plate_info.warrant_reason,
                "registration_date": plate_info.registration_date.isoformat(),
                "is_stolen": plate_info.is_stolen
            })
        else:
            fake_data = {
            "plate": "TJX 9717",
            "owner_name": "Matias Pena",
            "dob": "01/13/2004",
            "has_warrant": True,
            "registration_date": "09/28/2025",
            "license_ex_date": "12/31/2025",
            "warrant_reason": "Hello!",
            "is_stolen": True
          }
            # return JSONResponse(status_code=404, content={"detail": f"License plate {plate} not found"})
            return JSONResponse(status_code=203, content=fake_data)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {e}")
    
@app.post("/extract-all-plates-base64", response_model=List[ExtractResponse])
async def extract_all_plates_base64(request: Base64ImageRequest):
    """Extract all license plates from base64 image data (sent in request body)"""
    try:
        base64_image = request.base64_image.strip()
        
        # Handle base64 string (same validation as original)
        try:
            if base64_image.startswith('data:image/'):
                image_ref = base64_image
            else:
                import urllib.parse
                base64_clean = urllib.parse.unquote(base64_image)
                base64_clean = ''.join(base64_clean.split())
                
                try:
                    decoded_data = base64.b64decode(base64_clean, validate=True)
                except Exception:
                    raise HTTPException(status_code=400, detail="Invalid base64 encoding")
                
                if len(decoded_data) < 100:
                    raise HTTPException(status_code=400, detail="Base64 data too small to be a valid image")
                
                image_type = imghdr.what(None, h=decoded_data)
                if not image_type:
                    if decoded_data.startswith(b'\xFF\xD8\xFF'):
                        image_type = 'jpeg'
                    elif decoded_data.startswith(b'\x89PNG\r\n\x1a\n'):
                        image_type = 'png'
                    elif decoded_data.startswith(b'GIF87a') or decoded_data.startswith(b'GIF89a'):
                        image_type = 'gif'
                    else:
                        image_type = 'jpeg'
                
                image_ref = f"data:image/{image_type};base64,{base64_clean}"
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {e}")
        
        # Process the image to get all plates
        plates = askopenai_list(image_ref)
        
        # Remove spaces and filter out UNKNOWN plates
        valid_plates = [plate.replace(" ", "") for plate in plates if plate != "UNKNOWN"]
        
        if not valid_plates:
            return JSONResponse(status_code=404, content={"detail": "No license plates found in image"})
        
        results = []
        
        for plate in valid_plates:
            # Look up plate info
            plate_info = lookup_plate(plate)
            
            if plate_info:
                results.append({
                    "plate": plate,
                    "owner_name": plate_info.owner_name,
                    "dob": plate_info.dob.isoformat(),
                    "has_warrant": plate_info.has_warrant,
                    "warrant_reason": plate_info.warrant_reason,
                    "registration_date": plate_info.registration_date.isoformat(),
                    "is_stolen": plate_info.is_stolen
                })
            else:
                # Use fake data for plates not found
                results.append({
                    "plate": plate,
                    "owner_name": "UNKNOWN",
                    "dob": "UNKNOWN",
                    "has_warrant": False,
                    "warrant_reason": "UNKNOWN",
                    "registration_date": "UNKNOWN",
                    "is_stolen": False
                })
        
        return JSONResponse(status_code=200, content=results)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {e}")
    

@app.get("/plate/{plate_number}", response_model=PlateSearchResult)
async def lookup_plate_info(plate_number: str):
    """Look up license plate information and check for alerts"""
    result = search_plates_with_alerts(plate_number)
    if not result.found:
        raise HTTPException(status_code=404, detail="License plate not found")
    return result

@app.get("/plates", response_model=List[LicensePlateResponse])
async def get_all_license_plates():
    """Get all license plates in the database"""
    plates = get_all_plates()
    return [LicensePlateResponse(**plate.model_dump()) for plate in plates]

@app.post("/plate", response_model=dict)
async def add_license_plate(plate_data: LicensePlate):
    """Add a new license plate to the database"""
    success = add_plate(plate_data)
    if success:
        return {"message": f"License plate {plate_data.plate_number} added successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to add license plate")

@app.delete("/plate/{plate_number}", response_model=dict)
async def delete_license_plate(plate_number: str):
    """Remove a license plate from the database"""
    success = remove_plate(plate_number)
    if success:
        return {"message": f"License plate {plate_number} removed successfully"}
    else:
        raise HTTPException(status_code=404, detail="License plate not found")

@app.get("/plate/{plate_number}/alerts", response_model=List[str])
async def get_plate_alerts(plate_number: str):
    """Get alerts for a specific license plate"""
    result = search_plates_with_alerts(plate_number)
    if not result.found:
        raise HTTPException(status_code=404, detail="License plate not found")
    return result.alerts