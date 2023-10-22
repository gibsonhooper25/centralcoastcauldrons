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
            sqlalchemy.text("""SELECT sku, name, SUM(potion_transactions.potion_quantity_change) AS quantity, price, red_ml, green_ml, blue_ml, dark_ml FROM potion_transactions JOIN potions ON potions.id=potion_transactions.potion_id
                                WHERE quantity > 0  GROUP BY sku, name, quantity, price, red_ml, green_ml, blue_ml, dark_ml ORDER BY quantity desc LIMIT 6"""))
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
