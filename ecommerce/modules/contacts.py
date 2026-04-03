#!/usr/bin/env python3
"""Contacts management - people with communication methods."""

from utils.storage import load_data, save_data, generate_id
from utils.display import (print_success, print_error, print_warning, print_table,
                            print_header, print_info, prompt, prompt_choice, confirm)

CONTACT_TYPES = ["عميل", "تاجر", "كلاهما"]
COMM_METHODS = ["phone", "whatsapp", "email", "telegram", "other"]
COMM_LABELS = {"phone": "هاتف", "whatsapp": "واتساب", "email": "بريد إلكتروني",
               "telegram": "تيليغرام", "other": "أخرى"}


def _load():
    return load_data("contacts.json")


def _save(data):
    return save_data("contacts.json", data)


# ── Core functions ───────────────────────────────────────────────────────────

def add_contact(name, contact_type, communications, notes=""):
    """Add contact. communications = [{"method": ..., "value": ...}]"""
    data = _load()
    contact = {
        "id": generate_id("c"),
        "name": name.strip(),
        "type": contact_type,
        "communication": communications,
        "notes": notes.strip(),
    }
    data["contacts"].append(contact)
    if _save(data):
        return True, contact["id"], f"تمت إضافة جهة الاتصال: {name}"
    return False, None, "فشل الحفظ."


def list_contacts(contact_type=None):
    contacts = _load()["contacts"]
    if contact_type:
        contacts = [c for c in contacts if c.get("type") == contact_type or c.get("type") == "كلاهما"]
    return contacts


def get_contact(contact_id):
    for c in _load()["contacts"]:
        if c["id"] == contact_id:
            return c
    return None


def search_contacts(query):
    query = query.lower()
    results = []
    for c in _load()["contacts"]:
        if query in c["name"].lower():
            results.append(c)
            continue
        for comm in c.get("communication", []):
            if query in comm.get("value", "").lower():
                results.append(c)
                break
    return results


def update_contact(contact_id, updates):
    data = _load()
    for i, c in enumerate(data["contacts"]):
        if c["id"] == contact_id:
            data["contacts"][i].update(updates)
            if _save(data):
                return True, "تم التحديث."
            return False, "فشل الحفظ."
    return False, "جهة الاتصال غير موجودة."


def delete_contact(contact_id):
    data = _load()
    before = len(data["contacts"])
    data["contacts"] = [c for c in data["contacts"] if c["id"] != contact_id]
    if len(data["contacts"]) == before:
        return False, "جهة الاتصال غير موجودة."
    if _save(data):
        return True, "تم الحذف."
    return False, "فشل الحفظ."


def format_contact_row(c):
    comms = "; ".join(f"{COMM_LABELS.get(x['method'], x['method'])}: {x['value']}"
                      for x in c.get("communication", []))
    return (c["id"], c["name"], c.get("type", ""), comms, c.get("notes", ""))


# ── CLI menus ────────────────────────────────────────────────────────────────

def menu_add_contact():
    print_header("إضافة جهة اتصال")
    name = prompt("الاسم")
    if not name:
        return

    type_idx = prompt_choice(CONTACT_TYPES, "نوع جهة الاتصال")
    if type_idx < 0:
        return
    contact_type = CONTACT_TYPES[type_idx]

    communications = []
    while True:
        print_info("إضافة طريقة تواصل (أو اتركها فارغة للانتهاء)")
        method_idx = prompt_choice(list(COMM_LABELS.values()), "طريقة التواصل")
        if method_idx < 0:
            break
        method = COMM_METHODS[method_idx]
        value = prompt(f"أدخل {list(COMM_LABELS.values())[method_idx]}")
        if value:
            communications.append({"method": method, "value": value})
        if not confirm("إضافة طريقة تواصل أخرى؟"):
            break

    notes = prompt("ملاحظات (اختياري)")
    ok, cid, msg = add_contact(name, contact_type, communications, notes)
    print_success(msg) if ok else print_error(msg)


def menu_list_contacts():
    print_header("قائمة جهات الاتصال")
    contacts = list_contacts()
    rows = [format_contact_row(c) for c in contacts]
    print_table(["ID", "الاسم", "النوع", "التواصل", "ملاحظات"], rows)


def menu_search_contacts():
    print_header("بحث عن جهة اتصال")
    query = prompt("ابحث بالاسم أو رقم الهاتف")
    if not query:
        return
    results = search_contacts(query)
    rows = [format_contact_row(c) for c in results]
    print_table(["ID", "الاسم", "النوع", "التواصل", "ملاحظات"], rows, title=f"نتائج البحث عن: {query}")


def pick_contact(label="اختر جهة اتصال"):
    """Interactive contact picker. Returns contact dict or None."""
    contacts = list_contacts()
    if not contacts:
        print_warning("لا توجد جهات اتصال. أضف واحدة أولاً.")
        return None
    names = [f"{c['name']} ({c['id']})" for c in contacts]
    idx = prompt_choice(names, label)
    if idx < 0:
        return None
    return contacts[idx]


def menu():
    while True:
        print_header("جهات الاتصال")
        options = ["إضافة جهة اتصال", "عرض الكل", "بحث"]
        choice = prompt_choice(options, "اختر العملية")
        if choice == -1:
            break
        elif choice == 0:
            menu_add_contact()
        elif choice == 1:
            menu_list_contacts()
        elif choice == 2:
            menu_search_contacts()
        input("\n  اضغط Enter للمتابعة...")
