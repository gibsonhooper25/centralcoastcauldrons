from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.
    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("SELECT num_red_potions, num_blue_potions, num_green_potions FROM global_inventory"))
    potion_inventory = result.first()
    num_red_potions = potion_inventory.num_red_potions
    num_blue_potions = potion_inventory.num_blue_potions
    num_green_potions = potion_inventory.num_green_potions
    potential_catalog = [
        {
            "sku": "RED_POTION_0",
            "name": "red potion",
            "quantity": num_red_potions,
            "price": 50,
            "potion_type": [100, 0, 0, 0],
        },
        {
            "sku": "GREEN_POTION_0",
            "name": "green potion",
            "quantity": num_green_potions,
            "price": 50,
            "potion_type": [0, 100, 0, 0],
        },
        {
            "sku": "BLUE_POTION_0",
            "name": "blue potion",
            "quantity": num_blue_potions,
            "price": 5,
            "potion_type": [0, 0, 100, 0],
        }
    ]
    shown_catalog = []
    for item in potential_catalog:
        if item["quantity"] > 0:
            shown_catalog.append(item)
    print("SHOWN CATALOG = ")
    print(shown_catalog)

    return shown_catalog
