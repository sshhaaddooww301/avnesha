"""
Settings API endpoints.

Manages dynamic detection thresholds, risk weights, severity intervals,
and rule activation states directly in PostgreSQL.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import SystemSetting, DetectionRule as DetectionRuleModel
from app.schemas import SettingsResponse, SettingsUpdate
from app.engine.rules import RULE_REGISTRY

router = APIRouter(prefix="/api/settings", tags=["Settings"])

DEFAULT_SETTINGS = {
    "severity_low_max": 24,
    "severity_medium_max": 49,
    "severity_high_max": 74,
    "weight_deviation": 0.30,
    "weight_verification": 0.25,
    "weight_frequency": 0.15,
    "weight_anomaly": 0.20,
    "weight_hash_mismatch": 0.10,
    "deviation_threshold": 0.30,
    "zscore_threshold": 2.5,
    "replay_window_seconds": 300,
    "anomaly_sensitivity": 0.5,
}


@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Retrieve all current system settings and rule configurations."""
    result = await db.execute(select(SystemSetting))
    db_settings = {s.key: s.value for s in result.scalars().all()}

    # Merge with defaults
    def get_val(key, default):
        val = db_settings.get(key, default)
        if isinstance(val, dict) and "value" in val:
            return val["value"]
        return val

    severity_thresholds = {
        "low_max": get_val("severity_low_max", DEFAULT_SETTINGS["severity_low_max"]),
        "medium_max": get_val("severity_medium_max", DEFAULT_SETTINGS["severity_medium_max"]),
        "high_max": get_val("severity_high_max", DEFAULT_SETTINGS["severity_high_max"]),
    }

    risk_weights = {
        "weight_deviation": get_val("weight_deviation", DEFAULT_SETTINGS["weight_deviation"]),
        "weight_verification": get_val("weight_verification", DEFAULT_SETTINGS["weight_verification"]),
        "weight_frequency": get_val("weight_frequency", DEFAULT_SETTINGS["weight_frequency"]),
        "weight_anomaly": get_val("weight_anomaly", DEFAULT_SETTINGS["weight_anomaly"]),
        "weight_hash_mismatch": get_val("weight_hash_mismatch", DEFAULT_SETTINGS["weight_hash_mismatch"]),
    }

    detection_thresholds = {
        "deviation_threshold": get_val("deviation_threshold", DEFAULT_SETTINGS["deviation_threshold"]),
        "zscore_threshold": get_val("zscore_threshold", DEFAULT_SETTINGS["zscore_threshold"]),
        "replay_window_seconds": get_val("replay_window_seconds", DEFAULT_SETTINGS["replay_window_seconds"]),
        "anomaly_sensitivity": get_val("anomaly_sensitivity", DEFAULT_SETTINGS["anomaly_sensitivity"]),
    }

    # Fetch rules from DB
    rules_res = await db.execute(select(DetectionRuleModel))
    rules = rules_res.scalars().all()

    rule_list = [
        {
            "rule_id": r.rule_id,
            "name": r.name,
            "description": r.description,
            "enabled": r.enabled,
            "parameters": r.parameters,
        }
        for r in rules
    ]

    return {
        "severity_thresholds": severity_thresholds,
        "risk_weights": risk_weights,
        "detection_thresholds": detection_thresholds,
        "detection_rules": rule_list,
    }


@router.put("")
async def update_settings(
    update_data: SettingsUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Update runtime settings in PostgreSQL.
    Validated to prevent math poisoning, negative weights, and invalid severity thresholds.
    """
    flat_updates = {}
    data_dict = update_data.model_dump(exclude_unset=True)

    if "severity_thresholds" in data_dict and data_dict["severity_thresholds"]:
        st = data_dict["severity_thresholds"]
        if "low_max" in st and st["low_max"] is not None: flat_updates["severity_low_max"] = st["low_max"]
        if "medium_max" in st and st["medium_max"] is not None: flat_updates["severity_medium_max"] = st["medium_max"]
        if "high_max" in st and st["high_max"] is not None: flat_updates["severity_high_max"] = st["high_max"]

    if "risk_weights" in data_dict and data_dict["risk_weights"]:
        rw = data_dict["risk_weights"]
        for k, v in rw.items():
            if v is not None:
                flat_updates[k] = float(v)

    if "detection_thresholds" in data_dict and data_dict["detection_thresholds"]:
        dt = data_dict["detection_thresholds"]
        for k, v in dt.items():
            if v is not None:
                flat_updates[k] = float(v) if not isinstance(v, int) else v

    # Handle direct fields
    direct_keys = [
        "severity_low_max", "severity_medium_max", "severity_high_max",
        "weight_deviation", "weight_verification", "weight_frequency",
        "weight_anomaly", "weight_hash_mismatch", "deviation_threshold",
        "zscore_threshold", "replay_window_seconds", "anomaly_sensitivity"
    ]
    for k in direct_keys:
        if k in data_dict and data_dict[k] is not None:
            flat_updates[k] = data_dict[k]

    # Validate logical consistency
    low = flat_updates.get("severity_low_max")
    med = flat_updates.get("severity_medium_max")
    high = flat_updates.get("severity_high_max")
    if low and med and low >= med:
        raise HTTPException(status_code=400, detail="severity_low_max must be strictly less than severity_medium_max")
    if med and high and med >= high:
        raise HTTPException(status_code=400, detail="severity_medium_max must be strictly less than severity_high_max")

    for key, value in flat_updates.items():
        result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = {"value": value}
        else:
            db.add(SystemSetting(key=key, value={"value": value}))

    await db.commit()
    return {"status": "success", "updated_keys": list(flat_updates.keys())}


@router.patch("/rules/{rule_id}")
async def toggle_rule(
    rule_id: str,
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Enable or disable a specific detection rule."""
    result = await db.execute(select(DetectionRuleModel).where(DetectionRuleModel.rule_id == rule_id))
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if "enabled" in body:
        rule.enabled = bool(body["enabled"])
    if "parameters" in body:
        rule.parameters = body["parameters"]

    await db.commit()
    await db.refresh(rule)

    return {
        "rule_id": rule.rule_id,
        "enabled": rule.enabled,
        "parameters": rule.parameters,
    }
