#!/usr/bin/env python3
"""Profits, sales, and debt reports."""

from utils.display import (print_header, print_info, print_warning, print_table,
                            prompt, prompt_choice)
import modules.currency as currency_mod
import modules.contacts as contacts_mod
import modules.products as products_mod
import modules.sales as sales_mod
import modules.debts as debts_mod
import modules.inventory as inventory_mod


def sales_report(date_from=None, date_to=None, target_currency=None):
    """Return sales summary: total revenue, total profit, per-product breakdown."""
    orders = sales_mod.list_sales(date_from, date_to)
    if not orders:
        return {"total_revenue": {}, "total_profit": {}, "by_product": {}, "order_count": 0}

    total_revenue = {}
    total_profit = {}
    by_product = {}

    for order in orders:
        cur = order["currency"]
        rev = order["total"]
        prof = order["profit"]

        if target_currency and cur != target_currency:
            converted_rev, _ = currency_mod.convert(rev, cur, target_currency)
            converted_prof, _ = currency_mod.convert(prof, cur, target_currency)
            if converted_rev is not None:
                cur_key = target_currency
                rev = converted_rev
                prof = converted_prof if converted_prof is not None else 0
            else:
                cur_key = cur
        else:
            cur_key = cur

        total_revenue[cur_key] = total_revenue.get(cur_key, 0) + rev
        total_profit[cur_key] = total_profit.get(cur_key, 0) + prof

        for item in order.get("items", []):
            pid = item["product_id"]
            pname = item.get("product_name", pid)
            if pid not in by_product:
                by_product[pid] = {"name": pname, "qty_sold": 0, "revenue": {}, "profit": {}}
            by_product[pid]["qty_sold"] += item["quantity"]

            item_cur = item.get("payment_currency", item.get("currency", cur))
            item_rev = item.get("converted_price", item["unit_price"]) * item["quantity"]
            by_product[pid]["revenue"][item_cur] = by_product[pid]["revenue"].get(item_cur, 0) + item_rev

    return {
        "order_count": len(orders),
        "total_revenue": {k: round(v, 2) for k, v in total_revenue.items()},
        "total_profit": {k: round(v, 2) for k, v in total_profit.items()},
        "by_product": by_product,
    }


def debt_summary(target_currency=None):
    return debts_mod.debt_summary_by_currency(target_currency)


def inventory_summary():
    merchants = inventory_mod.list_merchants()
    result = []
    for m in merchants:
        contact = contacts_mod.get_contact(m["contact_id"])
        name = contact["name"] if contact else m["contact_id"]
        total_items = sum(inv["quantity"] for inv in m["inventory"])
        result.append({"merchant_id": m["id"], "name": name, "total_items": total_items,
                        "products": len(m["inventory"])})
    return result


# ── CLI menus ────────────────────────────────────────────────────────────────

def menu_sales_report():
    print_header("تقرير المبيعات والأرباح")

    date_from = prompt("من تاريخ (YYYY-MM-DD, اتركه فارغاً للكل)")
    date_to = prompt("إلى تاريخ (YYYY-MM-DD, اتركه فارغاً للكل)")

    currencies = currency_mod.list_currencies()
    cur_options = ["بدون تحويل"] + [f"{c['code']} - {c['name']}" for c in currencies]
    cur_idx = prompt_choice(cur_options, "تحويل التقرير إلى عملة")
    target = None
    if cur_idx > 0:
        target = currencies[cur_idx - 1]["code"]

    report = sales_report(
        date_from if date_from else None,
        date_to if date_to else None,
        target
    )

    print_info(f"عدد الطلبات: {report['order_count']}")
    print_info("إجمالي الإيرادات:")
    for cur, total in report["total_revenue"].items():
        print(f"    {total} {cur}")
    print_info("إجمالي الأرباح:")
    for cur, total in report["total_profit"].items():
        print(f"    {total} {cur}")

    if report["by_product"]:
        print_info("أداء المنتجات:")
        rows = [(p["name"], p["qty_sold"],
                 ", ".join(f"{round(v, 2)} {k}" for k, v in p["revenue"].items()))
                for p in report["by_product"].values()]
        print_table(["المنتج", "الكمية المباعة", "الإيراد"], rows)


def menu_debt_report():
    print_header("تقرير الديون")
    currencies = currency_mod.list_currencies()
    cur_options = ["بدون تحويل"] + [f"{c['code']} - {c['name']}" for c in currencies]
    cur_idx = prompt_choice(cur_options, "عرض بعملة")
    target = None
    if cur_idx > 0:
        target = currencies[cur_idx - 1]["code"]

    summary = debt_summary(target)
    label = f" (بـ {target})" if target else ""

    print_info(f"مدينون لي{label}:")
    if summary["owed_to_me"]:
        for cur, total in summary["owed_to_me"].items():
            print(f"    {round(total, 2)} {cur}")
    else:
        print("    لا يوجد")

    print_info(f"أنا المدين{label}:")
    if summary["i_owe"]:
        for cur, total in summary["i_owe"].items():
            print(f"    {round(total, 2)} {cur}")
    else:
        print("    لا يوجد")


def menu_inventory_report():
    print_header("تقرير المخزون")
    summary = inventory_summary()
    if not summary:
        print_warning("لا يوجد تجار مسجلون.")
        return
    rows = [(s["name"], s["products"], s["total_items"]) for s in summary]
    print_table(["التاجر", "عدد المنتجات", "إجمالي الكميات"], rows)


def menu():
    while True:
        print_header("التقارير والأرباح")
        options = ["تقرير المبيعات والأرباح", "تقرير الديون", "تقرير المخزون"]
        choice = prompt_choice(options, "اختر التقرير")
        if choice == -1:
            break
        elif choice == 0:
            menu_sales_report()
        elif choice == 1:
            menu_debt_report()
        elif choice == 2:
            menu_inventory_report()
        input("\n  اضغط Enter للمتابعة...")
