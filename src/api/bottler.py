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
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        inventory = result.first()
        red_potions = inventory.num_red_potions
        green_potions = inventory.num_green_potions
        blue_potions = inventory.num_blue_potions
        red_ml = inventory.num_red_ml
        green_ml = inventory.num_green_ml
        blue_ml = inventory.num_blue_ml
        for potion in potions_delivered:
            red_ml_used = potion.quantity * potion.potion_type[0]
            green_ml_used = potion.quantity * potion.potion_type[1]
            blue_ml_used = potion.quantity * potion.potion_type[2]
            red_ml -= red_ml_used
            green_ml -= green_ml_used
            blue_ml -= blue_ml_used
            if red_ml_used > green_ml_used and red_ml_used > blue_ml_used:
                red_potions += potion.quantity
            elif green_ml_used > blue_ml_used:
                green_potions += potion.quantity
            else:
                blue_potions += potion.quantity
        if red_ml >= 0 and green_ml >= 0 and blue_ml >= 0:
            connection.execute(
                sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions={red_potions}, num_red_ml={red_ml}, num_green_potions={green_potions}, num_green_ml={green_ml}, num_blue_potions={blue_potions}, num_blue_ml={blue_ml}"))

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
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml FROM global_inventory"))
    inventory = result.first()
    red_ml = inventory.num_red_ml
    green_ml = inventory.num_green_ml
    blue_ml = inventory.num_blue_ml
    red_potions_available = red_ml // 100
    green_potions_available = green_ml // 100
    blue_potions_available = blue_ml // 100
    potential_plan = [
        {
            "potion_type": [100, 0, 0, 0],
            "quantity": red_potions_available,
        },
        {
            "potion_type": [0, 100, 0, 0],
            "quantity": green_potions_available,
        },
        {
            "potion_type": [0, 0, 100, 0],
            "quantity": blue_potions_available,
        }
    ]
    given_plan = []
    for item in potential_plan:
        if item['quantity'] > 0:
            given_plan.append(item)
    return given_plan
