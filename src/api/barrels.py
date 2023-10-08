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
        for barrel in barrels_delivered:
            cost = barrel.quantity * barrel.price
            red_volume = barrel.quantity * barrel.ml_per_barrel * (barrel.potion_type[0]//100) # int division - assuming a barrel can only contain one color
            green_volume = barrel.quantity * barrel.ml_per_barrel * (barrel.potion_type[1] // 100) #inside parenthesis should return 1 or 0, overall units ml
            blue_volume = barrel.quantity * barrel.ml_per_barrel * (barrel.potion_type[2] // 100)
            num_red_ml += red_volume
            num_green_ml += green_volume
            num_blue_ml += blue_volume
            gold -= cost
        if gold >= 0:
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold={gold}, num_red_ml={num_red_ml}, num_green_ml={num_green_ml}, num_blue_ml={num_blue_ml}"))


    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print("CATALOG = ")
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        inventory = result.first()
        num_potions = inventory.num_red_potions + inventory.num_green_potions + inventory.num_blue_potions
        gold = inventory.gold
    catalog_quantities = []
    return_plan = []
    for barrel in wholesale_catalog:
        catalog_quantities.append(barrel.quantity)
        return_plan.append({"sku": barrel.sku, "quantity": 0})
    barrel_index = 0

    if num_potions < 10:
        #iterate through catalog repeatedly, adding one of each item until we're out of gold
        while gold >= 0:
            if catalog_quantities[barrel_index] > 0:
                #there's still some available to add to our plan from the catalog
                gold -= wholesale_catalog[barrel_index].price
                catalog_quantities[barrel_index] -= 1
                return_plan[barrel_index]["quantity"] += 1
            #wrap around
            barrel_index += 1
            if barrel_index == len(wholesale_catalog):
                barrel_index = 0

        #remove the last single item added to our plan so that we have positive gold
        return_plan[barrel_index-1]["quantity"] -= 1

    else: #don't buy anything if we have more than 10 total potions in our catalog
        return []
    for barrel in return_plan:
        if barrel["quantity"] == 0:
            return_plan.remove(barrel)
    print("BARRELS RETURN PLAN = ")
    print(return_plan)
    return return_plan

# [Barrel(sku='MEDIUM_RED_BARREL', ml_per_barrel=2500, potion_type=[1, 0, 0, 0], price=250, quantity=10),
#  Barrel(sku='SMALL_RED_BARREL', ml_per_barrel=500, potion_type=[1, 0, 0, 0], price=100, quantity=10),
#  Barrel(sku='MEDIUM_GREEN_BARREL', ml_per_barrel=2500, potion_type=[0, 1, 0, 0], price=250, quantity=10),
#  Barrel(sku='SMALL_GREEN_BARREL', ml_per_barrel=500, potion_type=[0, 1, 0, 0], price=100, quantity=10),
#  Barrel(sku='MEDIUM_BLUE_BARREL', ml_per_barrel=2500, potion_type=[0, 0, 1, 0], price=300, quantity=10),
#  Barrel(sku='SMALL_BLUE_BARREL', ml_per_barrel=500, potion_type=[0, 0, 1, 0], price=120, quantity=10),
#  Barrel(sku='MINI_RED_BARREL', ml_per_barrel=200, potion_type=[1, 0, 0, 0], price=60, quantity=1),
#  Barrel(sku='MINI_GREEN_BARREL', ml_per_barrel=200, potion_type=[0, 1, 0, 0], price=60, quantity=1),
#  Barrel(sku='MINI_BLUE_BARREL', ml_per_barrel=200, potion_type=[0, 0, 1, 0], price=60, quantity=1)]