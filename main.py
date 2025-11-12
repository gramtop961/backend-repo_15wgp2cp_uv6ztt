import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Place

app = FastAPI(title="Karnataka Tourism API", description="API for historical and monumental places in Karnataka")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Karnataka Tourism API is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# Seed sample places if collection is empty (idempotent)
@app.post("/seed")
def seed_places():
    try:
        existing = get_documents("place", {}, limit=1)
        if existing:
            return {"status": "ok", "message": "Places already seeded"}

        sample_places = [
            {
                "name": "Hampi",
                "city": "Hosapete",
                "region": "Vijayanagara",
                "category": "UNESCO Site",
                "era": "Vijayanagara Empire",
                "description": "Ruins of the medieval capital with temples, bazaars, and boulder-strewn landscapes.",
                "images": [
                    "https://images.unsplash.com/photo-1563891217998-941dbb4f1cfa",
                    "https://images.unsplash.com/photo-1603988363607-81f9f0b62a1f"
                ],
                "latitude": 15.3350,
                "longitude": 76.4600,
                "opening_hours": "Sunrise to Sunset",
                "ticket_info": "ASI tickets available on-site",
                "tags": ["temples", "ruins", "heritage"]
            },
            {
                "name": "Mysore Palace",
                "city": "Mysuru",
                "region": "Mysuru",
                "category": "Palace",
                "era": "Wadiyar Dynasty",
                "description": "Grand royal residence known for its Indo-Saracenic architecture and illumination.",
                "images": [
                    "https://images.unsplash.com/photo-1600804340584-c7db2eacf0bf"
                ],
                "latitude": 12.3052,
                "longitude": 76.6552,
                "opening_hours": "10:00 AM - 5:30 PM",
                "ticket_info": "Entry fee applicable",
                "tags": ["palace", "architecture"]
            },
            {
                "name": "Gol Gumbaz",
                "city": "Vijayapura",
                "region": "Bijapur",
                "category": "Monument",
                "era": "Adil Shahi Dynasty",
                "description": "Mausoleum of Mohammed Adil Shah, famous for one of the largest domes in the world.",
                "images": [
                    "https://images.unsplash.com/photo-1626625142651-2b3f324b20b9"
                ],
                "latitude": 16.8302,
                "longitude": 75.7397,
                "opening_hours": "6:00 AM - 6:00 PM",
                "ticket_info": "Entry fee applicable",
                "tags": ["dome", "mausoleum"]
            },
            {
                "name": "Belur & Halebidu Temples",
                "city": "Hassan",
                "region": "Hassan",
                "category": "Temple",
                "era": "Hoysala Empire",
                "description": "Exquisite Hoysala architecture with intricate stone carvings.",
                "images": [
                    "https://images.unsplash.com/photo-1595475033193-9ae70d37a0aa"
                ],
                "latitude": 13.1623,
                "longitude": 75.8675,
                "opening_hours": "6:30 AM - 8:00 PM",
                "ticket_info": "Free entry",
                "tags": ["hoysala", "carvings"]
            }
        ]

        for p in sample_places:
            create_document("place", p)

        return {"status": "ok", "inserted": len(sample_places)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Public API
@app.get("/places")
def list_places(q: Optional[str] = None, category: Optional[str] = None):
    try:
        filter_dict = {}
        if q:
            # Simple text search across name/description/tags using regex
            import re
            regex = {"$regex": re.escape(q), "$options": "i"}
            filter_dict = {"$or": [
                {"name": regex},
                {"description": regex},
                {"tags": regex}
            ]}
        if category:
            filter_dict["category"] = category
        docs = get_documents("place", filter_dict)
        # Convert ObjectId to string
        for d in docs:
            d["_id"] = str(d["_id"]) if "_id" in d else None
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PlaceIn(BaseModel):
    name: str
    city: str
    region: Optional[str] = None
    category: str
    era: Optional[str] = None
    description: Optional[str] = None
    images: Optional[List[str]] = []
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    opening_hours: Optional[str] = None
    ticket_info: Optional[str] = None
    tags: Optional[List[str]] = []

@app.post("/places")
def add_place(place: PlaceIn):
    try:
        pid = create_document("place", place.dict())
        return {"id": pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
