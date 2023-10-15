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
        ml_inventory = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory")).first()
    red_ml = ml_inventory.num_red_ml
    green_ml = ml_inventory.num_green_ml
    blue_ml = ml_inventory.num_blue_ml
    dark_ml = ml_inventory.num_dark_ml
    with db.engine.begin() as connection:
        recipes = connection.execute(sqlalchemy.text("SELECT sku, quantity, red_ml, green_ml, blue_ml, dark_ml FROM potions ORDER BY price desc")).all()
    first_plan = []
    total_potions = 0
    for recipe in recipes:
        first_plan.append({
            "potion_type": [recipe.red_ml, recipe.green_ml, recipe.blue_ml, recipe.dark_ml],
            "quantity": 0,
        })
        total_potions += recipe.quantity
    potion_index = 0
    consecutive_skips = 0
    while total_potions <= 300:
        recipe = recipes[potion_index]
        if red_ml >= recipe.red_ml and green_ml >= recipe.green_ml and blue_ml >= recipe.blue_ml and dark_ml >= recipe.dark_ml:
            #can mix
            red_ml -= recipe.red_ml
            green_ml -= recipe.green_ml
            blue_ml -= recipe.blue_ml
            dark_ml -= recipe.dark_ml
            first_plan[potion_index]['quantity'] += 1
            total_potions += 1
            consecutive_skips = 0
        else:
            consecutive_skips += 1
            if consecutive_skips == len(recipes):
                #iterated over every recipe without being able to mix one
                break
        potion_index += 1
        if potion_index == len(recipes):
            potion_index = 0
    if potion_index > 0:
        first_plan[potion_index-1]['quantity'] -= 1
    else:
        first_plan[len(recipes)-1]['quantity'] -= 1
    return_plan = []
    for potion in first_plan:
        if potion['quantity'] > 0:
            return_plan.append(potion)
    print("RETURN BOTTLE PLAN = ")
    print(return_plan)
    return return_plan
