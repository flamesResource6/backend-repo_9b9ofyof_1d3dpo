"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    phone: str = Field(..., description="Mobile phone number in E.164 or local format")
    name: Optional[str] = Field(None, description="Full name")
    is_verified: bool = Field(False, description="Whether user's phone is verified via OTP")
    last_login: Optional[str] = Field(None, description="ISO timestamp of last login")

class Restaurant(BaseModel):
    """Restaurant collection schema"""
    name: str = Field(..., description="Restaurant name")
    description: Optional[str] = Field(None, description="Short description")
    address: Optional[str] = Field(None, description="Street address")
    image: Optional[str] = Field(None, description="Image URL")
    rating: Optional[float] = Field(4.5, ge=0, le=5)
    cuisine: Optional[str] = Field(None, description="Cuisine type, e.g., Indian, Italian")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    image: Optional[str] = Field(None, description="Image URL")
    restaurant_id: Optional[str] = Field(None, description="Related restaurant _id as string")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags like spicy, veg")
