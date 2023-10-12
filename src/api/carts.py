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
        connection.execute(sqlalchemy.text(f"INSERT INTO carts (customer, total_price) VALUES ('{new_cart.customer}', 0)"))
        cart_id = connection.execute(sqlalchemy.text(f"SELECT id FROM carts WHERE customer = '{new_cart.customer}'")).first().id
    return {"cart_id": cart_id}


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
        potion = connection.execute(sqlalchemy.text(f"SELECT id, price FROM potions WHERE sku = '{item_sku}'"))
        potion = potion.first()
        connection.execute(sqlalchemy.text(f"INSERT INTO cart_items (item_key, quantity, cart_id) VALUES ({potion.id}, {cart_item.quantity}, {cart_id})"))
        additional_price = cart_item.quantity * potion.price
        current_price = connection.execute(sqlalchemy.text(f"SELECT total_price FROM carts WHERE id = {cart_id}")).first().total_price
        new_price = additional_price + current_price
        connection.execute(sqlalchemy.text(f"UPDATE carts SET total_price = {new_price} WHERE id = {cart_id}"))
        return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    with db.engine.begin() as connection:
        cart = connection.execute(sqlalchemy.text(f"SELECT * FROM carts WHERE id = {cart_id}"))
        cart = cart.first()
        cart_items = connection.execute(sqlalchemy.text(f"SELECT * FROM cart_items WHERE cart_id = {cart_id}"))
        remaining_quantities = []
        for item in cart_items:
            print("CART ITEM = " + str(item))
            quantity_desired = item.quantity
            quantity_available = connection.execute(sqlalchemy.text(f"SELECT quantity FROM potions WHERE id = {item.item_key}")).first().quantity
            quantity_remaining = quantity_available - quantity_desired
            if quantity_remaining >= 0:
                remaining_quantities.append({
                    "id": item.item_key,
                    "quantity": quantity_remaining
                })
            else:
                return {"success": False}
        print("CART " + str(cart_id) + " PAID " + str(cart.total_price))
        for bought_potion in remaining_quantities:
            connection.execute(sqlalchemy.text(f"UPDATE potions SET quantity = {bought_potion['quantity']} WHERE id = {bought_potion['id']}"))
        current_gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first().gold
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {current_gold + cart.total_price}"))
        connection.execute(sqlalchemy.text(f"DELETE FROM carts WHERE id = {cart.id}"))

        return {"success": True}
