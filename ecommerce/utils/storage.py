#!/usr/bin/env python3
"""JSON storage utilities with atomic writes and error fallback."""

import json
import os
import time
import uuid

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

DEFAULT_STRUCTURES = {
    "currencies.json": {"currencies": [], "exchange_rates": {}},
    "contacts.json": {"contacts": []},
    "products.json": {"products": []},
    "orders.json": {"orders": []},
    "debts.json": {"debts": []},
    "inventory.json": {"merchants": [], "transfers": []},
    "errors.json": {"errors": []},
}


def load_data(filename):
    """Load JSON file with fallback to empty structure on any error."""
    filepath = os.path.join(DATA_DIR, filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return DEFAULT_STRUCTURES.get(filename, {})
    except (json.JSONDecodeError, IOError):
        return DEFAULT_STRUCTURES.get(filename, {})


def save_data(filename, data):
    """Atomic write: save to .tmp first, then rename. Returns True on success."""
    filepath = os.path.join(DATA_DIR, filename)
    tmp_path = filepath + ".tmp"
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, filepath)
        return True
    except (IOError, OSError) as e:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return False


def load_config():
    """Load app config."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        return {
            "slack_webhook_url": "",
            "slack_enabled": False,
            "app_name": "نظام المتجر",
            "default_currency": "SAR",
        }


def generate_id(prefix=""):
    """Generate a unique short ID."""
    uid = str(uuid.uuid4())[:8]
    ts = str(int(time.time()))[-4:]
    return f"{prefix}{ts}{uid}"
