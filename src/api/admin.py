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


    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE potions SET quantity = {DEFAULT_NUM_POTIONS}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {DEFAULT_GOLD}, num_red_ml = {DEFAULT_NUM_ML}, num_green_ml = {DEFAULT_NUM_ML}, num_dark_ml = {DEFAULT_NUM_ML}, num_blue_ml = {DEFAULT_NUM_ML}"))
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

