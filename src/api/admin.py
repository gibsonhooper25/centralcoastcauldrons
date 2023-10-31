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
    metadata_obj = sqlalchemy.MetaData()
    inventory_transactions = sqlalchemy.Table("inventory_transactions", metadata_obj, autoload_with=db.engine)
    potion_transactions = sqlalchemy.Table("potion_transactions", metadata_obj, autoload_with=db.engine)
    carts = sqlalchemy.Table("carts", metadata_obj, autoload_with=db.engine)
    cart_items = sqlalchemy.Table("cart_items", metadata_obj, autoload_with=db.engine)
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.delete(inventory_transactions))
        connection.execute(sqlalchemy.delete(potion_transactions))
        connection.execute(sqlalchemy.delete(carts))
        connection.execute(sqlalchemy.delete(cart_items))
    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    # TODO: Change me!
    return {
        "shop_name": "Potion Shop Near Me",
        "shop_owner": "Gibson Hooper",
    }

