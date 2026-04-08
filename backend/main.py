"""
RendelIt MVP - Backend FastAPI
Sirve productos con precios de tienda y competencia.
Calcula colores de pines para el mapa.
Recibe reportes de precio/stock de usuarios.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RendelIt API",
    description="Backend para el visualizador de precios RendelIt",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PRODUCTS_FILE = Path(__file__).parent.parent / "data" / "products.json"

STORES = [
    {
        "id": "maga_plus",
        "name": "MAGA+",
        "latitude": -34.7248095,
        "longitude": -58.2567359,
        "address": "Moreno 745, Quilmes, Buenos Aires",
    },
    {
        "id": "ramona",
        "name": "RAMONA",
        "latitude": -34.5711164,
        "longitude": -58.4457316,
        "address": "Av. Federico Lacroze 2477, CABA",
    },
    {
        "id": "anika_shop",
        "name": "Anika Shop",
        "latitude": -34.6045129,
        "longitude": -58.4578861,
        "address": "Av. S. Martín 2159, C1416 CABA",
    },
]


def _load_products() -> List[dict]:
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


products_db: List[dict] = _load_products()


class ReportIn(BaseModel):
    store_id: str
    product_id: str
    stock_level: int = Field(ge=1, le=5)
    reported_price: Optional[float] = None


class ReportOut(BaseModel):
    store_id: str
    product_id: str
    stock_level: int
    reported_price: Optional[float]
    created_at: str


reports_db: dict[str, dict] = {}


def _latest_report(store_id: str, product_id: str) -> Optional[dict]:
    return reports_db.get(f"{store_id}:{product_id}")


def _competition_ref(product: dict) -> Optional[float]:
    """Mayor precio de la competencia para un producto."""
    prices = product.get("competition_prices", {})
    values = [value for value in prices.values() if value is not None]
    return max(values) if values else None


@app.get("/api/products", tags=["Productos"])
async def get_products():
    """Devuelve todos los productos con precios de tienda y competencia."""
    return products_db


@app.get("/api/stores/pins", tags=["Mapa"])
async def get_store_pins(product_id: Optional[str] = None):
    """
    Devuelve info de pines para el mapa.
    Si se pasa product_id, calcula color para ese producto.
    Sin product_id, calcula color agregado (promedio de todos los productos).
    """
    if product_id:
        product = next((p for p in products_db if p["id"] == product_id), None)
        if not product:
            raise HTTPException(404, f"Producto {product_id} no encontrado")
        comp_avg = _competition_ref(product)
        result = []
        for store in STORES:
            store_price = product.get("store_prices", {}).get(store["id"])
            if store_price is not None and comp_avg is not None and comp_avg > 0:
                delta = ((store_price - comp_avg) / comp_avg) * 100
                pin_color = "green" if store_price <= comp_avg else "red"
            else:
                delta = None
                pin_color = "green"
            report = _latest_report(store["id"], product_id)
            result.append(
                {
                    **store,
                    "store_id": store["id"],
                    "pin_color": pin_color,
                    "store_price": store_price,
                    "competition_avg": comp_avg,
                    "delta_percentage": round(delta, 1) if delta is not None else None,
                    "stock_level": report["stock_level"] if report else None,
                    "reported_price": report["reported_price"] if report else None,
                    "last_updated": report["created_at"] if report else None,
                }
            )
        return result

    result = []
    for store in STORES:
        result.append(
            {
                **store,
                "store_id": store["id"],
                "pin_color": "red",
                "store_price": None,
                "competition_avg": None,
                "delta_percentage": None,
                "stock_level": None,
                "reported_price": None,
                "last_updated": None,
            }
        )
    return result


@app.post("/api/reports", tags=["Reportes"])
async def create_report(report: ReportIn):
    """Guarda un reporte de precio/stock de un usuario."""
    store_ids = [store["id"] for store in STORES]
    if report.store_id not in store_ids:
        raise HTTPException(404, f"Tienda {report.store_id} no encontrada")
    product = next((p for p in products_db if p["id"] == report.product_id), None)
    if not product:
        raise HTTPException(404, f"Producto {report.product_id} no encontrado")

    key = f"{report.store_id}:{report.product_id}"
    entry = {
        "store_id": report.store_id,
        "product_id": report.product_id,
        "stock_level": report.stock_level,
        "reported_price": report.reported_price,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    reports_db[key] = entry
    logger.info("Reporte guardado: %s", key)

    if report.reported_price is not None:
        product["store_prices"][report.store_id] = report.reported_price
        logger.info(
            "Precio actualizado: %s en %s -> $%s",
            report.product_id,
            report.store_id,
            report.reported_price,
        )

    comp_avg = _competition_ref(product)
    store_price = product.get("store_prices", {}).get(report.store_id)
    if store_price is not None and comp_avg is not None and comp_avg > 0:
        pin_color = "green" if store_price <= comp_avg else "red"
    else:
        pin_color = "red"
    entry["pin_color"] = pin_color

    return entry


@app.get("/health", tags=["Sistema"])
async def health_check():
    return {"status": "ok", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
