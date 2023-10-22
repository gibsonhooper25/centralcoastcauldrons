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
    red_ml = 0
    green_ml = 0
    blue_ml = 0
    dark_ml = 0
    for potion in potions_delivered:
        total_ml = [i * potion.quantity for i in potion.potion_type]
        red_ml -= total_ml[0]
        green_ml -= total_ml[1]
        blue_ml -= total_ml[2]
        dark_ml -= total_ml[3]
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(f"""INSERT INTO potion_transactions (customer, potion_id, potion_quantity_change)
                                                VALUES ('ME', (SELECT id FROM potions WHERE red_ml={potion.potion_type[0]} AND green_ml={potion.potion_type[1]} AND blue_ml={potion.potion_type[2]} AND dark_ml={potion.potion_type[3]} LIMIT 1), {potion.quantity})"""))
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"""INSERT INTO inventory_transactions (red_ml_change, green_ml_change, blue_ml_change, dark_ml_change)
                                           VALUES ({red_ml}, {green_ml}, {blue_ml}, {dark_ml})"""))
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
        ml_result = connection.execute(sqlalchemy.text("SELECT SUM(red_ml_change) AS red, SUM(green_ml_change) AS green, SUM(blue_ml_change) AS blue, SUM(dark_ml_change) AS dark FROM inventory_transactions")).first()
        ml_inventory = MLInventory(red=ml_result.red, green=ml_result.green, blue=ml_result.blue, dark=ml_result.dark)
    potion_inventory = []
    with db.engine.begin() as connection:
        quantities_by_id = connection.execute(sqlalchemy.text("SELECT potion_id, SUM(potion_quantity_change) AS quantity FROM potion_transactions GROUP BY potion_id"))
        for potion in quantities_by_id:
            recipe = connection.execute(sqlalchemy.text(f"SELECT red_ml, green_ml, blue_ml, dark_ml FROM potions WHERE potions.id={potion.potion_id}")).first()
            potion_inventory.append(PotionInventory(potion_type=[recipe.red_ml, recipe.green_ml, recipe.blue_ml, recipe.dark_ml], quantity=potion.quantity))

    first_plan = bottler_optimize(ml_inventory, potion_inventory)
    return_plan = []
    for potion in first_plan:
        if potion['quantity'] > 0:
            return_plan.append(potion)
    print("RETURN BOTTLE PLAN = ")
    print(return_plan)
    return return_plan

class MLInventory(BaseModel):
    red: int
    green: int
    blue: int
    dark: int
def bottler_optimize(ml_inventory: MLInventory, potion_inventory: list[PotionInventory]):
    plan = []
    total_potions = 0
    for recipe in potion_inventory:
        plan.append({
            "potion_type": [recipe.potion_type[0], recipe.potion_type[1], recipe.potion_type[2], recipe.potion_type[3]],
            "quantity": 0,
        })
        total_potions += recipe.quantity
    potion_index = 0
    consecutive_skips = 0
    while total_potions <= 300:
        recipe = potion_inventory[potion_index]
        if ml_inventory.red >= recipe.potion_type[0] and ml_inventory.green >= recipe.potion_type[1] and ml_inventory.blue >= recipe.potion_type[2] and ml_inventory.dark >= recipe.potion_type[3]:
            # can mix
            ml_inventory.red -= recipe.potion_type[0]
            ml_inventory.green -= recipe.potion_type[1]
            ml_inventory.blue -= recipe.potion_type[2]
            ml_inventory.dark -= recipe.potion_type[3]
            plan[potion_index]['quantity'] += 1
            total_potions += 1
            consecutive_skips = 0
        else:
            consecutive_skips += 1
            if consecutive_skips == len(potion_inventory):
                # iterated over every recipe without being able to mix one
                break
        potion_index += 1
        if potion_index == len(potion_inventory):
            potion_index = 0
    if potion_index > 0:
        plan[potion_index - 1]['quantity'] -= 1
    else:
        plan[len(potion_inventory) - 1]['quantity'] -= 1
    return plan
