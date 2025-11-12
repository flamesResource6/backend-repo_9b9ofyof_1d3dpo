import os
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import db, create_document, get_documents

app = FastAPI(title="Restaurant App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Utils ----------
from bson import ObjectId


def to_str_id(doc: dict) -> dict:
    if not doc:
        return doc
    d = doc.copy()
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    # convert nested ObjectIds if any
    for k, v in list(d.items()):
        if isinstance(v, ObjectId):
            d[k] = str(v)
    return d


# ---------- Schemas ----------
class SendOtpRequest(BaseModel):
    phone: str = Field(..., description="Mobile phone number")


class VerifyOtpRequest(BaseModel):
    phone: str
    otp: str


class RestaurantOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    image: Optional[str] = None
    rating: Optional[float] = None
    cuisine: Optional[str] = None


class ProductOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    price: float
    image: Optional[str] = None
    restaurant_id: Optional[str] = None
    tags: Optional[List[str]] = []


# ---------- Startup seed ----------
@app.on_event("startup")
def seed_data():
    if db is None:
        return
    # Seed restaurants
    if db["restaurant"].count_documents({}) == 0:
        restaurants = [
            {
                "name": "Spice Garden",
                "description": "Authentic Indian cuisine with a modern twist",
                "address": "123 Curry Ave",
                "image": "https://images.unsplash.com/photo-1544025162-d76694265947?q=80&w=1600&auto=format&fit=crop",
                "rating": 4.6,
                "cuisine": "Indian",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
            {
                "name": "Pasta Piazza",
                "description": "Fresh handmade pastas and rustic sauces",
                "address": "45 Roma Street",
                "image": "https://images.unsplash.com/photo-1523986371872-9d3ba2e2f642?q=80&w=1600&auto=format&fit=crop",
                "rating": 4.7,
                "cuisine": "Italian",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
        ]
        db["restaurant"].insert_many(restaurants)

    # Seed products (menu items)
    if db["product"].count_documents({}) == 0:
        # Map restaurants to ids
        rest_docs = list(db["restaurant"].find())
        rest_ids = {r["name"]: r["_id"] for r in rest_docs}
        products = [
            {
                "title": "Butter Chicken",
                "description": "Creamy tomato sauce with tender chicken",
                "price": 12.99,
                "image": "https://images.unsplash.com/photo-1604909052743-88e0b01e6e8b?q=80&w=1600&auto=format&fit=crop",
                "restaurant_id": str(rest_ids.get("Spice Garden")),
                "tags": ["spicy", "non-veg"],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
            {
                "title": "Paneer Tikka",
                "description": "Grilled cottage cheese with spices",
                "price": 9.5,
                "image": "https://images.unsplash.com/photo-1625944528146-1b02d4ca9d24?q=80&w=1600&auto=format&fit=crop",
                "restaurant_id": str(rest_ids.get("Spice Garden")),
                "tags": ["veg", "grill"],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
            {
                "title": "Penne Arrabbiata",
                "description": "Spicy tomato sauce with garlic and chili",
                "price": 10.99,
                "image": "https://images.unsplash.com/photo-1473093295043-cdd812d0e601?q=80&w=1600&auto=format&fit=crop",
                "restaurant_id": str(rest_ids.get("Pasta Piazza")),
                "tags": ["veg", "pasta"],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
        ]
        db["product"].insert_many(products)


# ---------- Generic endpoints ----------
@app.get("/")
def read_root():
    return {"message": "Restaurant API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


# ---------- Auth (Phone + OTP demo) ----------
@app.post("/auth/send-otp")
def send_otp(payload: SendOtpRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    phone = payload.phone.strip()
    if not phone:
        raise HTTPException(status_code=400, detail="Phone is required")
    # Demo OTP (in production, send via SMS provider)
    otp = "1234"

    # Upsert user
    user = db["user"].find_one({"phone": phone})
    now = datetime.now(timezone.utc).isoformat()
    if user:
        db["user"].update_one({"_id": user["_id"]}, {"$set": {"is_verified": False, "last_login": now}})
    else:
        db["user"].insert_one(
            {
                "phone": phone,
                "name": None,
                "is_verified": False,
                "last_login": now,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
        )

    # Return OTP in response for demo
    return {"success": True, "otp": otp, "message": "OTP generated. Use 1234 for demo."}


@app.post("/auth/verify")
def verify_otp(payload: VerifyOtpRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    phone = payload.phone.strip()
    if payload.otp != "1234":
        raise HTTPException(status_code=400, detail="Invalid OTP")
    user = db["user"].find_one({"phone": phone})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db["user"].update_one({"_id": user["_id"]}, {"$set": {"is_verified": True, "updated_at": datetime.now(timezone.utc)}})
    return {"success": True, "user": to_str_id(db["user"].find_one({"_id": user["_id"]}))}


# ---------- Restaurants ----------
@app.get("/restaurants", response_model=List[RestaurantOut])
def list_restaurants():
    if db is None:
        return []
    docs = list(db["restaurant"].find())
    return [RestaurantOut(**to_str_id(d)) for d in docs]


@app.get("/restaurants/{restaurant_id}", response_model=RestaurantOut)
def get_restaurant(restaurant_id: str):
    if db is None:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        doc = db["restaurant"].find_one({"_id": ObjectId(restaurant_id)}) if ObjectId.is_valid(restaurant_id) else db["restaurant"].find_one({"_id": restaurant_id})
    except Exception:
        doc = None
    if not doc:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return RestaurantOut(**to_str_id(doc))


@app.get("/restaurants/{restaurant_id}/products", response_model=List[ProductOut])
def get_restaurant_products(restaurant_id: str):
    if db is None:
        return []
    docs = list(db["product"].find({"restaurant_id": restaurant_id}))
    return [ProductOut(**to_str_id(d)) for d in docs]


# ---------- Products ----------
@app.get("/products", response_model=List[ProductOut])
def list_products():
    if db is None:
        return []
    docs = list(db["product"].find())
    return [ProductOut(**to_str_id(d)) for d in docs]


@app.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: str):
    if db is None:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        doc = db["product"].find_one({"_id": ObjectId(product_id)}) if ObjectId.is_valid(product_id) else db["product"].find_one({"_id": product_id})
    except Exception:
        doc = None
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductOut(**to_str_id(doc))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
