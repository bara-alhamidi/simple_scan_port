#!/usr/bin/env python3
"""Debt management with multi-currency support."""

from datetime import datetime
from utils.storage import load_data, save_data, generate_id
from utils.display import (print_success, print_error, print_warning, print_table,
                            print_header, print_info, prompt, prompt_choice, confirm)
import modules.currency as currency_mod
import modules.contacts as contacts_mod
import modules.notifications as notif

DEBT_TYPES = ["مدين لي (عليه دين)", "أنا المدين (علي دين)"]
DEBT_TYPE_KEYS = ["owed_to_me", "i_owe"]


def _load():
    return load_data("debts.json")


def _save(data):
    return save_data("debts.json", data)


# ── Core functions ───────────────────────────────────────────────────────────

def add_debt(contact_id, amount, currency_code, debt_type, description=""):
    try:
        amount = float(amount)
        if amount <= 0:
            return False, None, "المبلغ يجب أن يكون أكبر من صفر."
    except (ValueError, TypeError):
        return False, None, "المبلغ يجب أن يكون رقماً."

    data = _load()
    debt = {
        "id": generate_id("d"),
        "contact_id": contact_id,
        "amount": amount,
        "currency": currency_code.upper(),
        "type": debt_type,
        "description": description.strip(),
        "date": datetime.now().date().isoformat(),
        "paid": False,
        "remaining": amount,
        "payments": [],
    }
    data["debts"].append(debt)
    if _save(data):
        return True, debt["id"], f"تم تسجيل الدين: {amount} {currency_code}"
    return False, None, "فشل الحفظ."


def record_payment(debt_id, amount, currency_code):
    """Record a payment toward a debt. Handles currency conversion."""
    try:
        amount = float(amount)
        if amount <= 0:
            return False, "المبلغ يجب أن يكون أكبر من صفر."
    except (ValueError, TypeError):
        return False, "المبلغ يجب أن يكون رقماً."

    data = _load()
    for i, debt in enumerate(data["debts"]):
        if debt["id"] == debt_id:
            if debt["paid"]:
                return False, "هذا الدين مسدد بالكامل."

            # Convert payment to debt currency if different
            if currency_code.upper() != debt["currency"]:
                converted, rate = currency_mod.convert(amount, currency_code, debt["currency"])
                if converted is None:
                    return False, f"لا يوجد سعر صرف بين {currency_code} و {debt['currency']}."
                payment_in_debt_currency = converted
            else:
                payment_in_debt_currency = amount
                rate = 1.0

            new_remaining = round(debt["remaining"] - payment_in_debt_currency, 4)
            if new_remaining < 0:
                new_remaining = 0

            payment_record = {
                "date": datetime.now().date().isoformat(),
                "amount": amount,
                "currency": currency_code.upper(),
                "converted_amount": payment_in_debt_currency,
                "debt_currency": debt["currency"],
                "exchange_rate": rate,
            }
            data["debts"][i]["payments"].append(payment_record)
            data["debts"][i]["remaining"] = new_remaining
            if new_remaining == 0:
                data["debts"][i]["paid"] = True

            if _save(data):
                status = "مسدد بالكامل" if new_remaining == 0 else f"المتبقي: {new_remaining} {debt['currency']}"
                return True, f"تم تسجيل الدفع. {status}"
            notif.log_error("debts.record_payment", "فشل الحفظ")
            return False, "فشل الحفظ."
    return False, "الدين غير موجود."


def mark_paid(debt_id):
    data = _load()
    for i, debt in enumerate(data["debts"]):
        if debt["id"] == debt_id:
            data["debts"][i]["paid"] = True
            data["debts"][i]["remaining"] = 0
            if _save(data):
                return True, "تم تسجيل الدين كمسدد."
            return False, "فشل الحفظ."
    return False, "الدين غير موجود."


def get_outstanding_debts():
    return [d for d in _load()["debts"] if not d["paid"]]


def get_debts_by_contact(contact_id):
    return [d for d in _load()["debts"] if d["contact_id"] == contact_id]


def get_all_debts():
    return _load()["debts"]


def debt_summary_by_currency(target_currency=None):
    """Summarize outstanding debts, optionally converted to a target currency."""
    debts = get_outstanding_debts()
    summary = {"owed_to_me": {}, "i_owe": {}}
    for debt in debts:
        dtype = debt["type"]
        cur = debt["currency"]
        remaining = debt["remaining"]

        if target_currency and cur != target_currency:
            converted, _ = currency_mod.convert(remaining, cur, target_currency)
            if converted is not None:
                cur = target_currency
                remaining = converted

        bucket = summary[dtype]
        bucket[cur] = bucket.get(cur, 0) + remaining

    return summary


def format_debt_row(d):
    contact = contacts_mod.get_contact(d.get("contact_id", ""))
    contact_name = contact["name"] if contact else d.get("contact_id", "")
    debt_label = "مدين لي" if d["type"] == "owed_to_me" else "أنا المدين"
    status = "مسدد" if d["paid"] else f"متبقي: {d['remaining']}"
    return (d["id"], contact_name, f"{d['amount']} {d['currency']}", debt_label,
            d["date"], status, d.get("description", ""))


# ── CLI menus ────────────────────────────────────────────────────────────────

def menu_add_debt():
    print_header("تسجيل دين جديد")
    contact = contacts_mod.pick_contact("اختر الشخص")
    if not contact:
        return

    currencies = currency_mod.list_currencies()
    if not currencies:
        print_warning("لا توجد عملات.")
        return
    cur_idx = prompt_choice([f"{c['code']} - {c['name']}" for c in currencies], "عملة الدين")
    if cur_idx < 0:
        return
    currency_code = currencies[cur_idx]["code"]

    amount_str = prompt("المبلغ")
    type_idx = prompt_choice(DEBT_TYPES, "نوع الدين")
    if type_idx < 0:
        return
    debt_type = DEBT_TYPE_KEYS[type_idx]
    description = prompt("الوصف (اختياري)")

    ok, did, msg = add_debt(contact["id"], amount_str, currency_code, debt_type, description)
    print_success(msg) if ok else print_error(msg)


def menu_record_payment():
    print_header("تسجيل دفعة")
    debts = get_outstanding_debts()
    if not debts:
        print_warning("لا توجد ديون غير مسددة.")
        return

    rows = [format_debt_row(d) for d in debts]
    print_table(["ID", "الشخص", "المبلغ", "النوع", "التاريخ", "الحالة", "الوصف"], rows)

    debt_id = prompt("أدخل ID الدين")
    debt = next((d for d in debts if d["id"] == debt_id), None)
    if not debt:
        print_error("الدين غير موجود.")
        return

    currencies = currency_mod.list_currencies()
    cur_idx = prompt_choice([f"{c['code']} - {c['name']}" for c in currencies], "عملة الدفعة")
    if cur_idx < 0:
        return
    pay_currency = currencies[cur_idx]["code"]

    amount_str = prompt(f"مبلغ الدفعة (المتبقي: {debt['remaining']} {debt['currency']})")
    ok, msg = record_payment(debt_id, amount_str, pay_currency)
    print_success(msg) if ok else print_error(msg)


def menu_list_debts():
    print_header("الديون")
    options = ["كل الديون", "غير المسددة فقط", "مسددة فقط"]
    choice = prompt_choice(options, "عرض")
    if choice < 0:
        return
    debts = get_all_debts()
    if choice == 1:
        debts = [d for d in debts if not d["paid"]]
    elif choice == 2:
        debts = [d for d in debts if d["paid"]]
    rows = [format_debt_row(d) for d in debts]
    print_table(["ID", "الشخص", "المبلغ", "النوع", "التاريخ", "الحالة", "الوصف"], rows)


def menu_debt_summary():
    print_header("ملخص الديون")
    currencies = currency_mod.list_currencies()
    print_warning("عرض الملخص بعملة محددة؟")
    cur_options = ["بدون تحويل (بعملتها الأصلية)"] + [f"{c['code']} - {c['name']}" for c in currencies]
    cur_idx = prompt_choice(cur_options, "العملة")
    target = None
    if cur_idx > 0:
        target = currencies[cur_idx - 1]["code"]

    summary = debt_summary_by_currency(target)
    label = f" (محول إلى {target})" if target else ""

    print_info(f"مدينون لي{label}:")
    for cur, total in summary["owed_to_me"].items():
        print(f"    {round(total, 2)} {cur}")
    print_info(f"أنا المدين{label}:")
    for cur, total in summary["i_owe"].items():
        print(f"    {round(total, 2)} {cur}")


def menu():
    while True:
        print_header("إدارة الديون")
        options = ["تسجيل دين", "تسجيل دفعة", "عرض الديون", "ملخص الديون"]
        choice = prompt_choice(options, "اختر العملية")
        if choice == -1:
            break
        elif choice == 0:
            menu_add_debt()
        elif choice == 1:
            menu_record_payment()
        elif choice == 2:
            menu_list_debts()
        elif choice == 3:
            menu_debt_summary()
        input("\n  اضغط Enter للمتابعة...")
