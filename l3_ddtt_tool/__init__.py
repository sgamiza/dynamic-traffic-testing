# -*- coding: utf-8 -*-
"""
:author: YOUR_NAME
:contact: YOUR_EMAIL
"""

__all__ = ["TestRunnerFactory", "IperfTestRunner", "BBUAlarmManager"]


def __getattr__(name):
    if name in ("TestRunnerFactory", "IperfTestRunner"):
        from .ddtt_main import IperfTestRunner, TestRunnerFactory

        return TestRunnerFactory if name == "TestRunnerFactory" else IperfTestRunner
    if name == "BBUAlarmManager":
        from .bbuapi import BBUAlarmManager

        return BBUAlarmManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
