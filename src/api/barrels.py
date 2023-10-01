from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    #Assuming this is atomic, so no barrels are delivered if the total cost of the barrel list is more than current gold
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        inventory = result.first()
        gold = inventory.gold
        num_red_ml = inventory.num_red_ml
        for barrel in barrels_delivered:
            cost = barrel.quantity * barrel.price
            volume = barrel.quantity * barrel.ml_per_barrel
            gold -= cost
            num_red_ml += volume
        if gold >= 0:
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold={gold}, num_red_ml={num_red_ml}"))


    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, gold FROM global_inventory"))
        inventory = result.first()
        num_potions = inventory.num_red_potions
        gold = inventory.gold
    quantity = 0
    if num_potions < 10 and wholesale_catalog[0].quantity > 0 and gold >= wholesale_catalog[0].price:
        quantity = 1


    return [
        {
            "sku": wholesale_catalog[0].sku,
            "quantity": quantity
        }
    ] if quantity > 0 else []
