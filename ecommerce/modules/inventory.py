#!/usr/bin/env python3
"""Merchant inventory management with custom exchange rates."""

from datetime import datetime
from utils.storage import load_data, save_data, generate_id
from utils.display import (print_success, print_error, print_warning, print_table,
                            print_header, print_info, prompt, prompt_choice, confirm)
import modules.currency as currency_mod
import modules.contacts as contacts_mod
import modules.products as products_mod
import modules.notifications as notif


def _load():
    return load_data("inventory.json")


def _save(data):
    return save_data("inventory.json", data)


# ── Core functions ───────────────────────────────────────────────────────────

def add_merchant(contact_id):
    data = _load()
    for m in data["merchants"]:
        if m["contact_id"] == contact_id:
            return False, None, "هذا التاجر مضاف بالفعل."
    merchant = {
        "id": generate_id("m"),
        "contact_id": contact_id,
        "inventory": [],
    }
    data["merchants"].append(merchant)
    if _save(data):
        return True, merchant["id"], "تم إضافة التاجر."
    return False, None, "فشل الحفظ."


def get_merchant(merchant_id):
    for m in _load()["merchants"]:
        if m["id"] == merchant_id:
            return m
    return None


def get_merchant_by_contact(contact_id):
    for m in _load()["merchants"]:
        if m["contact_id"] == contact_id:
            return m
    return None


def list_merchants():
    return _load()["merchants"]


def update_merchant_inventory(merchant_id, product_id, delta, cost_currency=None, custom_rate=None):
    """Add or subtract from merchant's inventory. delta can be negative."""
    data = _load()
    for i, merchant in enumerate(data["merchants"]):
        if merchant["id"] == merchant_id:
            # Find existing inventory entry for this product
            for j, inv in enumerate(merchant["inventory"]):
                if inv["product_id"] == product_id:
                    new_qty = inv["quantity"] + delta
                    if new_qty < 0:
                        return False, f"المخزون غير كافٍ. المتاح: {inv['quantity']}"
                    data["merchants"][i]["inventory"][j]["quantity"] = new_qty
                    if cost_currency:
                        data["merchants"][i]["inventory"][j]["cost_currency"] = cost_currency
                    if custom_rate is not None:
                        data["merchants"][i]["inventory"][j]["custom_rate"] = custom_rate
                    if _save(data):
                        return True, f"المخزون الجديد: {new_qty}"
                    return False, "فشل الحفظ."
            # New product entry
            if delta < 0:
                return False, "لا يوجد مخزون لهذا المنتج."
            data["merchants"][i]["inventory"].append({
                "product_id": product_id,
                "quantity": delta,
                "cost_currency": cost_currency or "SAR",
                "custom_rate": custom_rate,
            })
            if _save(data):
                return True, f"أضيف المنتج بكمية: {delta}"
            return False, "فشل الحفظ."
    return False, "التاجر غير موجود."


def transfer_stock(from_merchant_id, to_merchant_id, product_id, quantity, price, currency_code, custom_rate=None):
    """Transfer stock between merchants with optional custom exchange rate."""
    try:
        quantity = int(quantity)
        price = float(price)
        if quantity <= 0 or price < 0:
            return False, "الكمية والسعر يجب أن تكون موجبة."
    except (ValueError, TypeError):
        return False, "قيم غير صالحة."

    # Deduct from sender
    ok, msg = update_merchant_inventory(from_merchant_id, product_id, -quantity)
    if not ok:
        return False, f"فشل الخصم من المرسل: {msg}"

    # Add to receiver
    ok, msg = update_merchant_inventory(to_merchant_id, product_id, quantity, currency_code, custom_rate)
    if not ok:
        # Rollback
        update_merchant_inventory(from_merchant_id, product_id, quantity)
        notif.log_error("inventory.transfer_stock", f"فشل النقل وتم التراجع: {msg}")
        return False, f"فشل الإضافة للمستلم (تم التراجع): {msg}"

    # Log transfer
    data = _load()
    transfer = {
        "id": generate_id("t"),
        "date": datetime.now().isoformat(),
        "from_merchant": from_merchant_id,
        "to_merchant": to_merchant_id,
        "product_id": product_id,
        "quantity": quantity,
        "price": price,
        "currency": currency_code.upper(),
        "exchange_rate_used": custom_rate,
    }
    data["transfers"].append(transfer)
    _save(data)
    return True, f"تم نقل {quantity} وحدة بنجاح."


def list_transfers():
    return _load()["transfers"]


def view_merchant_inventory(merchant_id):
    merchant = get_merchant(merchant_id)
    if not merchant:
        return None
    result = []
    for inv in merchant["inventory"]:
        product = products_mod.get_product(inv["product_id"])
        p_name = product["name"] if product else inv["product_id"]
        result.append({
            "product_id": inv["product_id"],
            "product_name": p_name,
            "quantity": inv["quantity"],
            "cost_currency": inv.get("cost_currency", ""),
            "custom_rate": inv.get("custom_rate"),
        })
    return result


# ── CLI menus ────────────────────────────────────────────────────────────────

def menu_add_merchant():
    print_header("إضافة تاجر")
    contact = contacts_mod.pick_contact("اختر جهة الاتصال للتاجر")
    if not contact:
        return
    ok, mid, msg = add_merchant(contact["id"])
    print_success(msg) if ok else print_error(msg)


def menu_view_inventory():
    print_header("مخزون التجار")
    merchants = list_merchants()
    if not merchants:
        print_warning("لا يوجد تجار.")
        return
    options = []
    for m in merchants:
        contact = contacts_mod.get_contact(m["contact_id"])
        name = contact["name"] if contact else m["contact_id"]
        options.append(f"{name} ({m['id']})")
    idx = prompt_choice(options, "اختر التاجر")
    if idx < 0:
        return
    merchant = merchants[idx]
    contact = contacts_mod.get_contact(merchant["contact_id"])
    name = contact["name"] if contact else merchant["contact_id"]
    inv = view_merchant_inventory(merchant["id"])
    rows = [(i["product_name"], i["quantity"], i["cost_currency"],
             i["custom_rate"] if i["custom_rate"] else "افتراضي") for i in (inv or [])]
    print_table(["المنتج", "الكمية", "العملة", "سعر الصرف المخصص"], rows, title=f"مخزون: {name}")


def menu_transfer_stock():
    print_header("نقل مخزون بين التجار")
    merchants = list_merchants()
    if len(merchants) < 2:
        print_warning("تحتاج تاجرين على الأقل.")
        return

    def merchant_label(m):
        contact = contacts_mod.get_contact(m["contact_id"])
        return contact["name"] if contact else m["id"]

    labels = [merchant_label(m) for m in merchants]

    print_info("اختر المرسل:")
    idx1 = prompt_choice(labels, "المرسل")
    if idx1 < 0:
        return
    print_info("اختر المستلم:")
    idx2 = prompt_choice(labels, "المستلم")
    if idx2 < 0 or idx1 == idx2:
        print_error("اختر تاجرين مختلفين.")
        return

    from_m = merchants[idx1]
    to_m = merchants[idx2]

    product = products_mod.pick_product("اختر المنتج للنقل")
    if not product:
        return

    qty_str = prompt("الكمية")
    price_str = prompt("السعر")

    currencies = currency_mod.list_currencies()
    cur_idx = prompt_choice([f"{c['code']} - {c['name']}" for c in currencies], "عملة الصفقة")
    if cur_idx < 0:
        return
    currency_code = currencies[cur_idx]["code"]

    custom_rate_str = prompt("سعر صرف مخصص (اتركه فارغاً للاستخدام الافتراضي)")
    custom_rate = None
    if custom_rate_str:
        try:
            custom_rate = float(custom_rate_str)
        except ValueError:
            print_error("سعر الصرف غير صالح. سيستخدم الافتراضي.")

    ok, msg = transfer_stock(from_m["id"], to_m["id"], product["id"], qty_str, price_str, currency_code, custom_rate)
    print_success(msg) if ok else print_error(msg)


def menu_list_transfers():
    print_header("سجل النقل")
    transfers = list_transfers()
    rows = []
    for t in transfers:
        fm = get_merchant(t["from_merchant"])
        tm = get_merchant(t["to_merchant"])
        fc = contacts_mod.get_contact(fm["contact_id"]) if fm else None
        tc = contacts_mod.get_contact(tm["contact_id"]) if tm else None
        product = products_mod.get_product(t["product_id"])
        rows.append((
            t["id"], t["date"][:10],
            fc["name"] if fc else t["from_merchant"],
            tc["name"] if tc else t["to_merchant"],
            product["name"] if product else t["product_id"],
            t["quantity"], f"{t['price']} {t['currency']}",
            t.get("exchange_rate_used", "افتراضي")
        ))
    print_table(["ID", "التاريخ", "من", "إلى", "المنتج", "الكمية", "السعر", "سعر الصرف"], rows)


def menu():
    while True:
        print_header("جرد المخزون بين التجار")
        options = ["إضافة تاجر", "عرض مخزون تاجر", "نقل مخزون", "سجل النقل"]
        choice = prompt_choice(options, "اختر العملية")
        if choice == -1:
            break
        elif choice == 0:
            menu_add_merchant()
        elif choice == 1:
            menu_view_inventory()
        elif choice == 2:
            menu_transfer_stock()
        elif choice == 3:
            menu_list_transfers()
        input("\n  اضغط Enter للمتابعة...")
