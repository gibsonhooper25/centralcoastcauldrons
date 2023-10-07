from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

import src.api.carts
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

DEFAULT_NUM_POTIONS = 0
DEFAULT_NUM_ML = 0
DEFAULT_GOLD = 100

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    sql = "UPDATE global_inventory " \
          f"SET num_red_potions={DEFAULT_NUM_POTIONS}," \
          f"num_green_potions={DEFAULT_NUM_POTIONS}," \
          f"num_blue_potions={DEFAULT_NUM_POTIONS}," \
          f"num_red_ml={DEFAULT_NUM_ML}," \
          f"num_green_ml={DEFAULT_NUM_ML}," \
          f"num_blue_ml={DEFAULT_NUM_ML}," \
          f"gold={DEFAULT_GOLD}"

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql))
    src.api.carts.carts = []
    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    # TODO: Change me!
    return {
        "shop_name": "Potion Shop Near Me",
        "shop_owner": "Gibson Hooper",
    }

