from __future__ import annotations

import pytest

import polygres.version_notices as notice_module


@pytest.fixture(autouse=True)
def _disable_live_central_notice_checks() -> None:
    notice_module._central_notice_next_check = float("inf")
    notice_module._central_notice_etag = None
