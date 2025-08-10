from pydantic import BaseModel
from typing import List
from enum import Enum

class DietaryRestrictions(str, Enum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    HALAL = "halal"
    KOSHER = "kosher"
    GLUTEN_FREE = "gluten-free"
    DAIRY_FREE = "dairy-free"
    NUT_FREE = "nut-free"

class Query(BaseModel):
    question: str
    dietary_restrictions: List[DietaryRestrictions] = []

class Response(BaseModel):
    answer: str 


