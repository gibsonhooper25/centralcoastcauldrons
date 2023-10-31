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
    red_ml = 0
    green_ml = 0
    blue_ml = 0
    dark_ml = 0
    gold_change = 0
    for barrel in barrels_delivered:
        red_ml += barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[0]
        green_ml += barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[1]
        blue_ml += barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[2]
        dark_ml += barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[3]
        gold_change -= barrel.quantity * barrel.price
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"""INSERT INTO inventory_transactions (customer, gold_change, red_ml_change, green_ml_change, blue_ml_change, dark_ml_change) 
                                           VALUES ('ME', {gold_change}, {red_ml}, {green_ml}, {blue_ml}, {dark_ml})"""))
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print("WHOLESALE CATALOG = ")
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT SUM(gold_change) AS gold, SUM(red_ml_change) AS red, SUM(green_ml_change) AS green, SUM(blue_ml_change) AS blue, SUM(dark_ml_change) AS dark FROM inventory_transactions")).first()
        inventory = Inventory(gold=result.gold, red_ml=result.red, green_ml=result.green, blue_ml=result.blue, dark_ml=result.dark)
    return_plan = barrels_optimize(wholesale_catalog, inventory)
    final_plan = []
    for barrel in return_plan:
        if barrel["quantity"] > 0:
            final_plan.append(barrel)
    print("BARRELS RETURN PLAN = ")
    print(final_plan)
    return final_plan

class Inventory(BaseModel):
    gold: int
    red_ml: int
    green_ml: int
    blue_ml: int
    dark_ml: int
def barrels_optimize(catalog: list[Barrel], inventory: Inventory):
    plan = []
    catalog_total_quantity = 0
    consecutive_skips = 0
    remaining_gold = inventory.gold
    catalog = sorted(catalog, key=lambda b: b.ml_per_barrel / b.price, reverse=True)
    for barrel in catalog:
        plan.append({"sku": barrel.sku, "quantity": 0})
        catalog_total_quantity += barrel.quantity
    barrel_index = 0
    while consecutive_skips < len(catalog):
        item = catalog[barrel_index]
        if item.quantity > 0 and item.price <= remaining_gold:
            #there's still some available to add to our plan from the catalog
            remaining_gold -= item.price
            item.quantity -= 1
            plan[barrel_index]['quantity'] += 1
            consecutive_skips = 0
        else:
            consecutive_skips += 1
        barrel_index = (barrel_index + 1) % len(catalog)
    return plan
