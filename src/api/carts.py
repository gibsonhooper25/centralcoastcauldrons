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
    with db.engine.begin() as connection:
        cid = connection.execute(sqlalchemy.text(f"INSERT INTO carts (customer, total_price) VALUES ('{new_cart.customer}', 0) RETURNING id")).scalar_one()
    return {"cart_id": cid}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    with db.engine.begin() as connection:
        cart = connection.execute(sqlalchemy.text(f"SELECT * FROM carts WHERE id = {cart_id}"))
        cart = cart.first()
    if cart:
        return {
            "id": cart.id,
            "customer": cart.customer,
            "total_price": cart.total_price
        }
    else:
        return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"INSERT INTO cart_items (item_key, quantity, cart_id) VALUES ((SELECT id FROM potions WHERE sku='{item_sku}' LIMIT 1), {cart_item.quantity}, {cart_id})"))
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    with db.engine.begin() as connection:
        cart_items = connection.execute(sqlalchemy.text(f"""SELECT * FROM cart_items WHERE cart_items.cart_id={cart_id}"""))
        total_price = 0
        for item in cart_items:
            individual_price = connection.execute(sqlalchemy.text(f"""SELECT price FROM potions WHERE potions.id={item.item_key}""")).scalar_one()
            total_price += individual_price * item.quantity
            connection.execute(sqlalchemy.text(f"""INSERT INTO potion_transactions (customer, potion_id, potion_quantity_change)
                                                VALUES ((SELECT customer FROM carts WHERE carts.id={cart_id} LIMIT 1), {item.item_key}, {-item.quantity})"""))
        connection.execute(sqlalchemy.text(f"""INSERT INTO inventory_transactions (customer, gold_change)
                                                VALUES ((SELECT customer FROM carts WHERE carts.id={cart_id} LIMIT 1), {total_price})"""))
        connection.execute(sqlalchemy.text(f"DELETE FROM carts WHERE id = {cart_id}"))

        return {"success": True}
