#!/usr/bin/env python3
"""Currency and exchange rate management."""

from utils.storage import load_data, save_data
from utils.display import print_success, print_error, print_warning, print_table, print_header, prompt, prompt_choice, confirm


def _load():
    return load_data("currencies.json")


def _save(data):
    return save_data("currencies.json", data)


# ── Core functions ──────────────────────────────────────────────────────────

def add_currency(code, name, symbol):
    """Add a new currency. Returns (True, msg) or (False, msg)."""
    code = code.upper().strip()
    data = _load()
    for c in data["currencies"]:
        if c["code"] == code:
            return False, f"العملة {code} موجودة بالفعل."
    data["currencies"].append({"code": code, "name": name.strip(), "symbol": symbol.strip()})
    if _save(data):
        return True, f"تمت إضافة العملة: {name} ({code})"
    return False, "فشل الحفظ."


def list_currencies():
    return _load()["currencies"]


def get_currency(code):
    for c in _load()["currencies"]:
        if c["code"] == code.upper():
            return c
    return None


def set_exchange_rate(from_code, to_code, rate):
    """Set exchange rate: 1 from_code = rate to_code."""
    from_code = from_code.upper()
    to_code = to_code.upper()
    try:
        rate = float(rate)
        if rate <= 0:
            return False, "يجب أن يكون السعر أكبر من صفر."
    except (ValueError, TypeError):
        return False, "سعر الصرف يجب أن يكون رقماً."
    data = _load()
    key = f"{from_code}_{to_code}"
    data["exchange_rates"][key] = rate
    # Also set reverse if not already set
    reverse_key = f"{to_code}_{from_code}"
    if reverse_key not in data["exchange_rates"]:
        data["exchange_rates"][reverse_key] = round(1 / rate, 6)
    if _save(data):
        return True, f"1 {from_code} = {rate} {to_code}"
    return False, "فشل الحفظ."


def get_exchange_rate(from_code, to_code):
    """Get rate: 1 from_code = ? to_code. Returns None if not found."""
    from_code = from_code.upper()
    to_code = to_code.upper()
    if from_code == to_code:
        return 1.0
    rates = _load()["exchange_rates"]
    key = f"{from_code}_{to_code}"
    if key in rates:
        return rates[key]
    # Try reverse
    reverse = f"{to_code}_{from_code}"
    if reverse in rates:
        return round(1 / rates[reverse], 6)
    return None


def convert(amount, from_code, to_code):
    """Convert amount from one currency to another. Returns (converted_amount, rate) or (None, None)."""
    rate = get_exchange_rate(from_code, to_code)
    if rate is None:
        return None, None
    return round(float(amount) * rate, 4), rate


def list_rates():
    return _load()["exchange_rates"]


# ── CLI menus ────────────────────────────────────────────────────────────────

def menu_add_currency():
    print_header("إضافة عملة جديدة")
    code = prompt("رمز العملة (مثال: USD)")
    if not code:
        return
    name = prompt("اسم العملة (مثال: دولار أمريكي)")
    if not name:
        return
    symbol = prompt("رمز الكتابة (مثال: $)")
    if not symbol:
        symbol = code
    ok, msg = add_currency(code, name, symbol)
    print_success(msg) if ok else print_error(msg)


def menu_set_rate():
    print_header("تحديد سعر الصرف")
    currencies = list_currencies()
    if len(currencies) < 2:
        print_warning("تحتاج عملتين على الأقل.")
        return
    codes = [f"{c['code']} - {c['name']}" for c in currencies]

    print_warning("اختر العملة الأصلية (من):")
    idx1 = prompt_choice(codes, "العملة الأصلية")
    if idx1 < 0:
        return
    print_warning("اختر العملة المستهدفة (إلى):")
    idx2 = prompt_choice(codes, "العملة المستهدفة")
    if idx2 < 0 or idx1 == idx2:
        print_error("اختر عملتين مختلفتين.")
        return

    from_code = currencies[idx1]["code"]
    to_code = currencies[idx2]["code"]
    rate_str = prompt(f"سعر الصرف: 1 {from_code} = ? {to_code}")
    ok, msg = set_exchange_rate(from_code, to_code, rate_str)
    print_success(msg) if ok else print_error(msg)


def menu_list_currencies():
    print_header("العملات المتاحة")
    currencies = list_currencies()
    rows = [(c["code"], c["name"], c["symbol"]) for c in currencies]
    print_table(["الرمز", "الاسم", "الرمز الكتابي"], rows)


def menu_list_rates():
    print_header("أسعار الصرف")
    rates = list_rates()
    rows = [(k.replace("_", " → "), v) for k, v in rates.items()]
    print_table(["من → إلى", "السعر"], rows)


def menu():
    while True:
        print_header("العملات وأسعار الصرف")
        options = [
            "إضافة عملة جديدة",
            "تحديد سعر صرف",
            "عرض العملات",
            "عرض أسعار الصرف",
        ]
        choice = prompt_choice(options, "اختر العملية")
        if choice == -1:
            break
        elif choice == 0:
            menu_add_currency()
        elif choice == 1:
            menu_set_rate()
        elif choice == 2:
            menu_list_currencies()
        elif choice == 3:
            menu_list_rates()
        input("\n  اضغط Enter للمتابعة...")
