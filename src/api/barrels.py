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
    print("BARRELS DELIVERED = ")
    print(barrels_delivered)
    #Assuming this is atomic, so no barrels are delivered if the total cost of the barrel list is more than current gold
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        inventory = result.first()
        gold = inventory.gold
        num_red_ml = inventory.num_red_ml
        num_green_ml = inventory.num_green_ml
        num_blue_ml = inventory.num_blue_ml
        num_dark_ml = inventory.num_dark_ml
        for barrel in barrels_delivered:
            cost = barrel.quantity * barrel.price
            red_volume = barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[0]
            green_volume = barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[1]
            blue_volume = barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[2]
            dark_volume = barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[3]
            num_red_ml += red_volume
            num_green_ml += green_volume
            num_blue_ml += blue_volume
            num_dark_ml += dark_volume
            gold -= cost
        if gold >= 0:
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold={gold}, num_red_ml={num_red_ml}, num_green_ml={num_green_ml}, num_blue_ml={num_blue_ml}, num_dark_ml={num_dark_ml}"))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print("WHOLESALE CATALOG = ")
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        inventory = result.first()
        gold = inventory.gold
    return_plan = []
    catalog_total_quantity = 0
    for barrel in wholesale_catalog:
        return_plan.append({"sku": barrel.sku, "quantity": 0})
        catalog_total_quantity += barrel.quantity
    barrel_index = 0
    while gold >= 0 and catalog_total_quantity > 0:
        item = wholesale_catalog[barrel_index]
        if item.quantity > 0:
            #there's still some available to add to our plan from the catalog
            gold -= item.price
            catalog_total_quantity -= 1
            item.quantity -= 1
            return_plan[barrel_index]['quantity'] += 1
        barrel_index += 1
        if barrel_index == len(wholesale_catalog):
            barrel_index = 0
    if gold < 0:
        #remove the last single item added to our plan so that we have positive gold
        if barrel_index > 0:
            return_plan[barrel_index-1]["quantity"] -= 1
        else:
            return_plan[len(wholesale_catalog)-1]["quantity"] -= 1
    final_plan = []
    for barrel in return_plan:
        if barrel["quantity"] > 0:
            final_plan.append(barrel)
    print("BARRELS RETURN PLAN = ")
    print(final_plan)
    return final_plan
