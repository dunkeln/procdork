"""Opt-in Logfire setup for root-level end-to-end test runners."""

from __future__ import annotations

import os

import logfire


def configure_logfire() -> None:
    logfire.configure(
        service_name="procdork-tests",
        environment=os.environ.get("E2E_ENVIRONMENT", "local"),
        send_to_logfire="if-token-present",
        console=False,
        advanced=logfire.AdvancedOptions(
            base_url="https://logfire-us.pydantic.dev"
        ),
    )
