#!/usr/bin/env python3
"""Slack notifications with local fallback logging."""

import json
from datetime import datetime
from utils.storage import load_data, save_data, load_config


def log_error(context, error_msg):
    """Always log error locally to errors.json."""
    data = load_data("errors.json")
    if "errors" not in data:
        data["errors"] = []
    data["errors"].append({
        "timestamp": datetime.now().isoformat(),
        "context": context,
        "error": str(error_msg),
    })
    save_data("errors.json", data)


def send_slack_alert(message, error_details=None):
    """
    Send a Slack notification via webhook.
    Falls back to local log if Slack is disabled or fails.
    """
    config = load_config()
    webhook_url = config.get("slack_webhook_url", "")
    slack_enabled = config.get("slack_enabled", False)

    if not slack_enabled or not webhook_url or webhook_url == "PASTE_YOUR_SLACK_WEBHOOK_URL_HERE":
        log_error("slack_alert.skipped", f"{message} | {error_details}")
        return False, "Slack غير مفعّل. تم التسجيل محلياً."

    try:
        import requests
        payload = {
            "text": f":warning: *{config.get('app_name', 'نظام المتجر')}*\n{message}",
            "attachments": [],
        }
        if error_details:
            payload["attachments"].append({
                "color": "danger",
                "text": str(error_details),
            })
        response = requests.post(webhook_url, json=payload, timeout=5)
        if response.status_code == 200:
            return True, "تم إرسال التنبيه إلى Slack."
        else:
            log_error("slack_alert.http_error", f"HTTP {response.status_code}: {response.text}")
            return False, f"فشل إرسال Slack (HTTP {response.status_code}). تم التسجيل محلياً."
    except ImportError:
        log_error("slack_alert.import_error", "مكتبة requests غير متوفرة")
        return False, "مكتبة requests غير متوفرة. تم التسجيل محلياً."
    except Exception as e:
        log_error("slack_alert.exception", str(e))
        return False, f"خطأ في الإرسال: {e}. تم التسجيل محلياً."


def notify_error(context, error_msg):
    """Log locally and attempt Slack notification."""
    log_error(context, error_msg)
    send_slack_alert(f"خطأ في: {context}", error_msg)
