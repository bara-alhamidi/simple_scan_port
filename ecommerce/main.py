#!/usr/bin/env python3
"""
نظام المتجر الإلكتروني - المبيعات والديون والجرد
Main entry point - CLI menu
"""

import sys
import os

# Add ecommerce directory to path so modules can import each other
sys.path.insert(0, os.path.dirname(__file__))

from utils.display import print_header, print_info, print_error, print_success, prompt_choice, clear_screen
from utils.storage import load_config

import modules.currency as currency_mod
import modules.contacts as contacts_mod
import modules.products as products_mod
import modules.sales as sales_mod
import modules.debts as debts_mod
import modules.inventory as inventory_mod
import modules.reports as reports_mod
import modules.notifications as notif


MENU_ITEMS = [
    ("💱  العملات وأسعار الصرف",    currency_mod.menu),
    ("👥  جهات الاتصال",            contacts_mod.menu),
    ("📦  إدارة المنتجات",           products_mod.menu),
    ("🛒  المبيعات والطلبات",        sales_mod.menu),
    ("💸  إدارة الديون",             debts_mod.menu),
    ("🏪  جرد المخزون (التجار)",     inventory_mod.menu),
    ("📊  التقارير والأرباح",         reports_mod.menu),
]


def show_banner(config):
    clear_screen()
    app_name = config.get("app_name", "نظام المتجر")
    default_cur = config.get("default_currency", "SAR")
    print_header(f"{app_name}  |  العملة الافتراضية: {default_cur}")
    print_info("نظام متكامل للمبيعات · الديون · الجرد · التقارير")
    print()


def main():
    config = load_config()
    while True:
        show_banner(config)
        labels = [label for label, _ in MENU_ITEMS]
        choice = prompt_choice(labels, "القائمة الرئيسية")
        if choice == -1:
            print_success("إلى اللقاء!")
            break
        try:
            _, handler = MENU_ITEMS[choice]
            handler()
        except KeyboardInterrupt:
            print()
            continue
        except Exception as e:
            print_error(f"خطأ غير متوقع: {e}")
            notif.notify_error("main.menu", str(e))
            input("\n  اضغط Enter للمتابعة...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nتم الخروج.")
        sys.exit(0)
