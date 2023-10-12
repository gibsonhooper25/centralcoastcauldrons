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
    print("POTIONS DELIVERED = ")
    print(potions_delivered)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
    raw_inventory = result.first()
    red_ml = raw_inventory.num_red_ml
    green_ml = raw_inventory.num_green_ml
    blue_ml = raw_inventory.num_blue_ml
    dark_ml = raw_inventory.num_dark_ml
    red_bottled = 0
    green_bottled = 0
    blue_bottled = 0
    dark_bottled = 0
    for potion in potions_delivered:
        with db.engine.begin() as connection:
            potion_info = connection.execute(sqlalchemy.text(f"SELECT sku, quantity FROM potions WHERE red_ml={potion.potion_type[0]} AND green_ml={potion.potion_type[1]} AND blue_ml={potion.potion_type[2]} AND dark_ml={potion.potion_type[3]}")).first()
            sku = potion_info.sku
            quantity = potion_info.quantity
            total_ml = [i * potion.quantity for i in potion.potion_type]
            red_bottled += total_ml[0]
            green_bottled += total_ml[1]
            blue_bottled += total_ml[2]
            dark_bottled += total_ml[3]
            connection.execute(sqlalchemy.text(f"UPDATE potions SET quantity={quantity + potion.quantity} WHERE sku='{sku}'"))

    with db.engine.begin() as connection:
        connection.execute(
                sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml={red_ml - red_bottled}, num_green_ml={green_ml - green_bottled}, num_blue_ml={blue_ml - blue_bottled}, num_dark_ml={dark_ml - dark_bottled}"))

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
    red_ml_plain = red_ml // 2
    red_ml_mix = red_ml - red_ml_plain
    green_potions_available = green_ml // 100
    blue_ml_plain = blue_ml // 2
    blue_ml_mix = blue_ml - blue_ml_plain
    purple_mix_num = min(red_ml_mix, blue_ml_mix) // 50
    potential_plan = [
        {
            "potion_type": [100, 0, 0, 0],
            "quantity": red_ml_plain // 100,
        },
        {
            "potion_type": [0, 100, 0, 0],
            "quantity": green_potions_available,
        },
        {
            "potion_type": [0, 0, 100, 0],
            "quantity": blue_ml_plain // 100,
        },
        {
            "potion_type": [50, 0, 50, 0],
            "quantity": purple_mix_num,
        }
    ]
    given_plan = []
    for item in potential_plan:
        if item['quantity'] > 0:
            given_plan.append(item)
    print("RETURN BOTTLE PLAN = ")
    print(given_plan)
    return given_plan
