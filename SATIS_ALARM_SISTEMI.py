#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kök dizinde eksik olan SalesAlarmSystem köprüsü."""

from datetime import datetime


class SalesAlarmSystem:
    """Tam sürüm alt klasörlerde; kök panel importları için güvenli yedek."""

    def __init__(self):
        self.alerts = []
        self.last_check = datetime.now()

    def get_sales_summary(self):
        return {
            "alerts_count": len(self.alerts),
            "last_check": self.last_check.isoformat(),
            "source": "root_stub",
        }
