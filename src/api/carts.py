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
    cart = []
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
    print("SET QUANTITY BEFORE = ")
    print(cart)
    item_already_in_cart = False
    for i in range(len(cart)):
        if cart[i]["sku"] == item_sku:
            cart[i]["quantity"] = cart_item.quantity
            item_already_in_cart = True
            break
    if not item_already_in_cart:
        cart.append({"sku": item_sku, "quantity": cart_item.quantity})
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    cart = carts[cart_id]
    print("CART = ")
    print(cart)
    print("PAYMENT = " + cart_checkout.payment)
    gold_paid = 0
    red_bought = 0
    green_bought = 0
    blue_bought = 0
    for i in range(len(cart)): #for each item in the cart
        item = cart[i]
        quantity = item["quantity"]
        match item["sku"]:
            case "RED_POTION_0":
                red_bought += quantity
                gold_paid += quantity * 50
            case "GREEN_POTION_0":
                green_bought += quantity
                gold_paid += quantity * 50
            case "BLUE_POTION_0":
                blue_bought += quantity
                gold_paid += quantity * 5
            case _:
                return {"success": False}
        #gold_paid += quantity * 25 #hard coded price right not
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        inventory = result.first()
        gold = inventory.gold + gold_paid
        num_red_potions = inventory.num_red_potions - red_bought
        num_green_potions = inventory.num_green_potions - green_bought
        num_blue_potions = inventory.num_blue_potions - blue_bought
        if num_red_potions >= 0 and num_green_potions >= 0 and num_blue_potions >= 0:
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions={num_red_potions}, num_green_potions={num_green_potions}, num_blue_potions={num_blue_potions}, gold={gold}"))
            carts[cart_id] = []
            print("CHECKOUT SUCCESS")
            return {"success": True}
        else:
            print("CHECKOUT FAIL")
            return {"success": False}
