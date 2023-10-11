from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        potions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions"))
        num_potions = 0
        for row in potions:
            num_potions += row.quantity
        raw_inventory = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        raw_inventory = raw_inventory.first()
        num_ml = raw_inventory.num_red_ml + raw_inventory.num_green_ml + raw_inventory.num_blue_ml
        gold = raw_inventory.gold
    return {"number_of_potions": num_potions, "ml_in_barrels": num_ml, "gold": gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
