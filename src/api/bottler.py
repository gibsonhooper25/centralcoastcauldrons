from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print(potions_delivered)
    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        inventory = inventory.first()
        red_potions = inventory.num_red_potions
        red_ml = inventory.num_red_ml
        for potion in potions_delivered:
            red_ml_used = 100 * potion.quantity
            red_ml -= red_ml_used
            red_potions += potion.quantity
        if red_ml > 0:
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions={red_potions}, num_red_ml={red_ml}"))



    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))
    num_red_ml_inventory = result.first().num_red_ml
    num_potions_available = num_red_ml_inventory/100

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": num_potions_available,
            }
        ]
