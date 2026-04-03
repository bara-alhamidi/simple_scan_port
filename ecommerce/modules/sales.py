#!/usr/bin/env python3
"""Sales and orders management."""

from datetime import datetime
from utils.storage import load_data, save_data, generate_id
from utils.display import (print_success, print_error, print_warning, print_table,
                            print_header, print_info, prompt, prompt_choice, confirm)
import modules.currency as currency_mod
import modules.contacts as contacts_mod
import modules.products as products_mod
import modules.notifications as notif


def _load():
    return load_data("orders.json")


def _save(data):
    return save_data("orders.json", data)


# ── Core functions ───────────────────────────────────────────────────────────

def new_sale(contact_id, items, payment_currency):
    """
    Create a new sale.
    items = [{"product_id": ..., "quantity": ..., "unit_price": ..., "currency": ...}]
    Returns (True, order_id, msg) or (False, None, msg)
    """
    # Validate and convert prices, deduct stock
    total_in_payment_currency = 0.0
    total_profit = 0.0
    enriched_items = []

    for item in items:
        product = products_mod.get_product(item["product_id"])
        if not product:
            return False, None, f"المنتج {item['product_id']} غير موجود."
        qty = int(item["quantity"])
        if qty <= 0:
            return False, None, "الكمية يجب أن تكون أكبر من صفر."
        if product["stock"] < qty:
            return False, None, f"المخزون غير كافٍ للمنتج: {product['name']}. المتاح: {product['stock']}"

        unit_price = float(item.get("unit_price", product["sale_price"]))
        item_currency = item.get("currency", product["currency"])

        # Convert sale price to payment currency
        converted_price, rate = currency_mod.convert(unit_price, item_currency, payment_currency)
        if converted_price is None:
            return False, None, f"لا يوجد سعر صرف بين {item_currency} و {payment_currency}."

        # Profit: (sale_price - cost_price) in product currency, then converted
        margin = unit_price - product["cost_price"]
        profit_converted, _ = currency_mod.convert(margin * qty, item_currency, payment_currency)
        if profit_converted is None:
            profit_converted = margin * qty  # fallback: use as-is

        total_in_payment_currency += converted_price * qty
        total_profit += profit_converted

        enriched_items.append({
            "product_id": product["id"],
            "product_name": product["name"],
            "quantity": qty,
            "unit_price": unit_price,
            "currency": item_currency,
            "converted_price": converted_price,
            "payment_currency": payment_currency,
            "exchange_rate": rate,
        })

    # Deduct stock for all items atomically
    for item in enriched_items:
        ok, msg = products_mod.update_stock(item["product_id"], -item["quantity"])
        if not ok:
            notif.log_error("sales.new_sale.update_stock", msg)
            return False, None, f"فشل خصم المخزون: {msg}"

    # Save order
    data = _load()
    order = {
        "id": generate_id("o"),
        "date": datetime.now().isoformat(),
        "contact_id": contact_id,
        "items": enriched_items,
        "total": round(total_in_payment_currency, 4),
        "currency": payment_currency,
        "profit": round(total_profit, 4),
        "status": "completed",
    }
    data["orders"].append(order)
    if _save(data):
        return True, order["id"], f"تمت عملية البيع بنجاح. الإجمالي: {order['total']} {payment_currency}"
    notif.log_error("sales.new_sale.save", "فشل حفظ الطلب")
    return False, None, "فشل حفظ الطلب."


def list_sales(date_from=None, date_to=None):
    orders = _load()["orders"]
    if date_from:
        orders = [o for o in orders if o["date"] >= date_from]
    if date_to:
        orders = [o for o in orders if o["date"] <= date_to]
    return orders


def get_sale(order_id):
    for o in _load()["orders"]:
        if o["id"] == order_id:
            return o
    return None


def format_order_row(o):
    contact = contacts_mod.get_contact(o.get("contact_id", ""))
    contact_name = contact["name"] if contact else o.get("contact_id", "")
    items_count = len(o.get("items", []))
    return (o["id"], o["date"][:10], contact_name, items_count,
            f"{o['total']} {o['currency']}", f"{o['profit']} {o['currency']}", o["status"])


# ── CLI menus ────────────────────────────────────────────────────────────────

def menu_new_sale():
    print_header("بيع جديد")

    # Pick customer
    contact = contacts_mod.pick_contact("اختر العميل")
    if not contact:
        return

    # Pick payment currency
    currencies = currency_mod.list_currencies()
    if not currencies:
        print_warning("لا توجد عملات. أضف عملة أولاً.")
        return
    cur_idx = prompt_choice([f"{c['code']} - {c['name']}" for c in currencies], "عملة الدفع")
    if cur_idx < 0:
        return
    payment_currency = currencies[cur_idx]["code"]

    # Add items
    items = []
    while True:
        print_info(f"إضافة منتج للبيع (العملة: {payment_currency})")
        product = products_mod.pick_product()
        if not product:
            if not items:
                return
            break

        qty_str = prompt(f"الكمية (متاح: {product['stock']})", default=1)
        try:
            qty = int(qty_str)
        except ValueError:
            print_error("الكمية يجب أن تكون رقماً.")
            continue

        # Allow custom price
        default_price = product["sale_price"]
        price_str = prompt(f"السعر للوحدة ({product['currency']})", default=default_price)
        try:
            price = float(price_str)
        except ValueError:
            price = default_price

        items.append({
            "product_id": product["id"],
            "quantity": qty,
            "unit_price": price,
            "currency": product["currency"],
        })
        print_success(f"أضيف: {product['name']} × {qty}")

        if not confirm("إضافة منتج آخر؟"):
            break

    if not items:
        print_warning("لم تختر أي منتجات.")
        return

    # Summary
    print_info("ملخص البيع:")
    for item in items:
        p = products_mod.get_product(item["product_id"])
        print(f"  • {p['name']} × {item['quantity']} = {item['unit_price'] * item['quantity']} {item['currency']}")
    print(f"  عملة الدفع: {payment_currency}")

    if not confirm("تأكيد البيع؟"):
        return

    ok, oid, msg = new_sale(contact["id"], items, payment_currency)
    print_success(msg) if ok else print_error(msg)


def menu_list_sales():
    print_header("سجل المبيعات")
    orders = list_sales()
    rows = [format_order_row(o) for o in orders]
    print_table(["ID", "التاريخ", "العميل", "المنتجات", "الإجمالي", "الربح", "الحالة"], rows)


def menu_sale_details():
    print_header("تفاصيل طلب")
    oid = prompt("أدخل ID الطلب")
    order = get_sale(oid)
    if not order:
        print_error("الطلب غير موجود.")
        return
    print_info(f"طلب: {order['id']} | تاريخ: {order['date'][:10]}")
    print_info(f"الإجمالي: {order['total']} {order['currency']} | الربح: {order['profit']} {order['currency']}")
    rows = [(i["product_name"], i["quantity"], f"{i['unit_price']} {i['currency']}",
             f"{i['converted_price']} {i['payment_currency']}") for i in order["items"]]
    print_table(["المنتج", "الكمية", "السعر", "بعد التحويل"], rows)


def menu():
    while True:
        print_header("المبيعات والطلبات")
        options = ["بيع جديد", "عرض كل المبيعات", "تفاصيل طلب"]
        choice = prompt_choice(options, "اختر العملية")
        if choice == -1:
            break
        elif choice == 0:
            menu_new_sale()
        elif choice == 1:
            menu_list_sales()
        elif choice == 2:
            menu_sale_details()
        input("\n  اضغط Enter للمتابعة...")
