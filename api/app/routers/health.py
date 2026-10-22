from __future__ import annotations

import logging

from fastapi import APIRouter

from ..deps import SettingsDep, get_scenario_repo

router = APIRouter(tags=["stav"])
logger = logging.getLogger(__name__)


@router.get("/health")
def health(settings: SettingsDep) -> dict[str, str]:
    if not settings.db_configured:
        return {"status": "ok", "db": "not_configured"}
    try:
        get_scenario_repo(settings).ping()
    except Exception:
        logger.exception("Supabase ping zlyhal")
        return {"status": "ok", "db": "error"}
    return {"status": "ok", "db": "ok"}
