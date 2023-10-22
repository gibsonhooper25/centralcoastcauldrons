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
        num_potions = connection.execute(sqlalchemy.text("SELECT SUM(potion_quantity_change) FROM potion_transactions")).scalar_one()
        num_ml = connection.execute(sqlalchemy.text("SELECT SUM(red_ml_change + green_ml_change + blue_ml_change + dark_ml_change) FROM inventory_transactions")).scalar_one()
        gold = connection.execute(sqlalchemy.text("SELECT SUM(gold_change) FROM inventory_transactions")).scalar_one()
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
