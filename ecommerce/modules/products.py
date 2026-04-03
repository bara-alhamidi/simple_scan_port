#!/usr/bin/env python3
"""Product catalog management."""

from utils.storage import load_data, save_data, generate_id
from utils.display import (print_success, print_error, print_warning, print_table,
                            print_header, print_info, prompt, prompt_choice, confirm)
import modules.currency as currency_mod


def _load():
    return load_data("products.json")


def _save(data):
    return save_data("products.json", data)


# ── Core functions ───────────────────────────────────────────────────────────

def add_product(name, cost_price, sale_price, currency_code, stock, category=""):
    try:
        cost_price = float(cost_price)
        sale_price = float(sale_price)
        stock = int(stock)
    except (ValueError, TypeError):
        return False, None, "الأسعار والمخزون يجب أن تكون أرقاماً."
    if cost_price < 0 or sale_price < 0 or stock < 0:
        return False, None, "لا يمكن أن تكون القيم سالبة."

    data = _load()
    product = {
        "id": generate_id("p"),
        "name": name.strip(),
        "cost_price": cost_price,
        "sale_price": sale_price,
        "currency": currency_code.upper(),
        "stock": stock,
        "category": category.strip(),
    }
    data["products"].append(product)
    if _save(data):
        return True, product["id"], f"تمت إضافة المنتج: {name}"
    return False, None, "فشل الحفظ."


def get_product(product_id):
    for p in _load()["products"]:
        if p["id"] == product_id:
            return p
    return None


def list_products():
    return _load()["products"]


def update_stock(product_id, delta):
    """Add delta to stock (negative to subtract). Returns (True/False, msg)."""
    data = _load()
    for i, p in enumerate(data["products"]):
        if p["id"] == product_id:
            new_stock = p["stock"] + delta
            if new_stock < 0:
                return False, f"المخزون غير كافٍ. المتاح: {p['stock']}"
            data["products"][i]["stock"] = new_stock
            if _save(data):
                return True, f"المخزون الجديد: {new_stock}"
            return False, "فشل الحفظ."
    return False, "المنتج غير موجود."


def update_product(product_id, updates):
    data = _load()
    for i, p in enumerate(data["products"]):
        if p["id"] == product_id:
            data["products"][i].update(updates)
            if _save(data):
                return True, "تم التحديث."
            return False, "فشل الحفظ."
    return False, "المنتج غير موجود."


def format_product_row(p):
    cur = p.get("currency", "")
    margin = round(p["sale_price"] - p["cost_price"], 2)
    return (p["id"], p["name"], p.get("category", ""), f"{p['cost_price']} {cur}",
            f"{p['sale_price']} {cur}", f"{margin} {cur}", p["stock"])


# ── CLI menus ────────────────────────────────────────────────────────────────

def menu_add_product():
    print_header("إضافة منتج جديد")
    name = prompt("اسم المنتج")
    if not name:
        return
    category = prompt("الفئة (اختياري)")

    currencies = currency_mod.list_currencies()
    if not currencies:
        print_warning("لا توجد عملات. أضف عملة أولاً.")
        return
    cur_idx = prompt_choice([f"{c['code']} - {c['name']}" for c in currencies], "العملة")
    if cur_idx < 0:
        return
    cur_code = currencies[cur_idx]["code"]

    cost_str = prompt("سعر التكلفة")
    sale_str = prompt("سعر البيع")
    stock_str = prompt("الكمية في المخزون", default=0)

    ok, pid, msg = add_product(name, cost_str, sale_str, cur_code, stock_str, category)
    print_success(msg) if ok else print_error(msg)


def menu_list_products():
    print_header("المنتجات")
    rows = [format_product_row(p) for p in list_products()]
    print_table(["ID", "الاسم", "الفئة", "التكلفة", "سعر البيع", "الهامش", "المخزون"], rows)


def menu_update_stock():
    print_header("تعديل المخزون")
    products = list_products()
    if not products:
        print_warning("لا توجد منتجات.")
        return
    idx = prompt_choice([f"{p['name']} (مخزون: {p['stock']})" for p in products], "اختر المنتج")
    if idx < 0:
        return
    product = products[idx]
    delta_str = prompt("الكمية المضافة (سالبة للطرح)")
    try:
        delta = int(delta_str)
    except ValueError:
        print_error("أدخل رقماً صحيحاً.")
        return
    ok, msg = update_stock(product["id"], delta)
    print_success(msg) if ok else print_error(msg)


def pick_product(label="اختر منتجاً"):
    """Interactive product picker. Returns product dict or None."""
    products = list_products()
    if not products:
        print_warning("لا توجد منتجات. أضف منتجاً أولاً.")
        return None
    options = [f"{p['name']} - مخزون: {p['stock']} - {p['sale_price']} {p['currency']}" for p in products]
    idx = prompt_choice(options, label)
    if idx < 0:
        return None
    return products[idx]


def menu():
    while True:
        print_header("إدارة المنتجات")
        options = ["إضافة منتج", "عرض الكل", "تعديل المخزون"]
        choice = prompt_choice(options, "اختر العملية")
        if choice == -1:
            break
        elif choice == 0:
            menu_add_product()
        elif choice == 1:
            menu_list_products()
        elif choice == 2:
            menu_update_stock()
        input("\n  اضغط Enter للمتابعة...")
