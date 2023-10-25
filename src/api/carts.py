from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from enum import Enum

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku,
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


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
