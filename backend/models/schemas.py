"""
Modelos Pydantic para validacion de datos en la API.
"""
from typing import Dict, Optional

from pydantic import BaseModel


class Product(BaseModel):
    id: str
    name: str
    category: str
    brand: str
    presentation: str
    store_prices: Dict[str, float]
    competition_prices: Dict[str, float]


class StorePinInfo(BaseModel):
    store_id: str
    name: str
    latitude: float
    longitude: float
    address: str
    pin_color: str
    store_price: Optional[float] = None
    competition_avg: Optional[float] = None
    delta_percentage: Optional[float] = None
