from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalog = []
    # Can return a max of 20 items.
    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("SELECT * FROM potions WHERE quantity > 0 ORDER BY quantity desc LIMIT 6"))
    for potion in result:
        catalog.append({
            "sku": potion.sku,
            "name": potion.name,
            "quantity": potion.quantity,
            "price": potion.price,
            "potion_type": [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml]
        })
    print("SHOWN CATALOG = ")
    print(catalog)
    return catalog
