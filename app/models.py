from pydantic import BaseModel
from typing import Dict

class CarbonIntensityRecord(BaseModel):
    date: str
    intensity: float

class Preferences(BaseModel):
    customer_id: str
    preferences: Dict[str, str]
