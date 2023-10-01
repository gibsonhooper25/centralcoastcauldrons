from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

carts = []

class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    cart = {
        "customer": new_cart.customer,
        "items": [],
        "quantities": [],
        "prices": [],
        "num_items": 0
    }
    carts.append(cart)
    return {"cart_id": len(carts) - 1}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return carts[cart_id]


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    cart = carts[cart_id]
    index = -1
    for i in range(cart["num_items"]):
        if cart["items"][i] == item_sku:
            index = i
            break
    if index >= 0:
        cart["quantities"][index] += cart_item.quantity
    else:
        cart["items"].append(item_sku)
        cart["quantities"].append(cart_item.quantity)
        cart["prices"].append(50) #hard code price of red potion for now
        cart["num_items"] += 1

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    cart = carts[cart_id]
    num_potions_bought = 0
    gold_paid = 0
    for i in range(cart["num_items"]):
        num_potions_bought += cart["quantities"][i]
        gold_paid += cart["quantities"][i] * cart["prices"][i]
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        inventory = result.first()
        gold = inventory.gold + gold_paid
        num_red_potions = inventory.num_red_potions - num_potions_bought
        if num_red_potions >= 0:
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions={num_red_potions}, gold={gold}"))
            carts[cart_id] = {}
            return {"success": True}
        else:
            return {"success": False}
