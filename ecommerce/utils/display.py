#!/usr/bin/env python3
"""CLI display helpers using colorama and tabulate."""

import os
import sys

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORAMA_OK = True
except ImportError:
    COLORAMA_OK = False

try:
    from tabulate import tabulate
    TABULATE_OK = True
except ImportError:
    TABULATE_OK = False


def _color(text, color_code):
    if COLORAMA_OK:
        return color_code + str(text) + Style.RESET_ALL
    return str(text)


def print_success(msg):
    print(_color(f"✓ {msg}", Fore.LIGHTGREEN_EX if COLORAMA_OK else ""))


def print_error(msg):
    print(_color(f"✗ خطأ: {msg}", Fore.LIGHTRED_EX if COLORAMA_OK else ""))


def print_info(msg):
    print(_color(f"ℹ {msg}", Fore.LIGHTCYAN_EX if COLORAMA_OK else ""))


def print_warning(msg):
    print(_color(f"⚠ {msg}", Fore.LIGHTYELLOW_EX if COLORAMA_OK else ""))


def print_header(title):
    line = "═" * (len(title) + 4)
    print()
    if COLORAMA_OK:
        print(Fore.LIGHTBLUE_EX + f"╔{line}╗")
        print(Fore.LIGHTBLUE_EX + f"║  {title}  ║")
        print(Fore.LIGHTBLUE_EX + f"╚{line}╝" + Style.RESET_ALL)
    else:
        print(f"╔{line}╗")
        print(f"║  {title}  ║")
        print(f"╚{line}╝")
    print()


def print_table(headers, rows, title=None):
    if title:
        print_info(title)
    if not rows:
        print_warning("لا توجد بيانات للعرض.")
        return
    if TABULATE_OK:
        print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))
    else:
        # Simple fallback table
        col_widths = [max(len(str(h)), max((len(str(r[i])) for r in rows), default=0))
                      for i, h in enumerate(headers)]
        sep = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
        print(sep)
        header_row = "| " + " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths)) + " |"
        print(header_row)
        print(sep)
        for row in rows:
            print("| " + " | ".join(str(v).ljust(w) for v, w in zip(row, col_widths)) + " |")
        print(sep)


def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")


def prompt(msg, default=None):
    """Show a prompt and return stripped input."""
    suffix = f" [{default}]" if default is not None else ""
    try:
        val = input(_color(f"  → {msg}{suffix}: ", Fore.LIGHTYELLOW_EX if COLORAMA_OK else "")).strip()
        return val if val else (str(default) if default is not None else "")
    except (KeyboardInterrupt, EOFError):
        print()
        return ""


def prompt_choice(options, title="اختر"):
    """Show numbered options and return selected index (0-based) or -1 on cancel."""
    print_info(title)
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    print(f"  0. رجوع / إلغاء")
    val = prompt("اختيارك")
    try:
        idx = int(val)
        if idx == 0:
            return -1
        if 1 <= idx <= len(options):
            return idx - 1
        print_error("اختيار غير صالح.")
        return -1
    except ValueError:
        print_error("الرجاء إدخال رقم.")
        return -1


def confirm(msg):
    """Ask yes/no. Returns True for yes."""
    val = prompt(f"{msg} (y/n)").lower()
    return val in ("y", "yes", "نعم", "ن")
