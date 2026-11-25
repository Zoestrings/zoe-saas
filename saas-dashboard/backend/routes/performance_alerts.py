"""Token Performance Monitoring & Real-Time Dashboard Alerts API Routes."""

import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from zoe.scanner.performance_monitor import (
    ensure_performance_schema,
    get_monitored_token_by_id,
    get_platform_monitoring_settings,
    register_token_monitoring,
    run_performance_monitoring_cycle,
)
from zoe.tools.scanner import detect_chain, fetch_dexscreener_market_data

logger = logging.getLogger("zoe.api.performance_alerts")


class MonitorRegisterRequest(BaseModel):
    contract_address: str = Field(..., min_length=10, max_length=128)
    project_id: Optional[str] = None
    scan_id: Optional[str] = None
    positive_thresholds: Optional[List[float]] = None
    negative_thresholds: Optional[List[float]] = None
    drawdown_threshold_pct: Optional[float] = None


class MonitorUpdateRequest(BaseModel):
    monitoring_status: Optional[str] = None  # "active" | "paused" | "stopped"
    positive_thresholds: Optional[List[float]] = None
    negative_thresholds: Optional[List[float]] = None
    drawdown_threshold_pct: Optional[float] = None


class AdminMonitorSettingsRequest(BaseModel):
    default_positive_thresholds: Optional[List[float]] = None
    default_negative_thresholds: Optional[List[float]] = None
    max_monitored_free: Optional[int] = Field(default=None, ge=1, le=500)
    max_monitored_pro: Optional[int] = Field(default=None, ge=1, le=2000)
    polling_interval_seconds: Optional[int] = Field(default=None, ge=60, le=3600)


def _get_user_plan(conn: Any, user_id: str, role: str) -> str:
    if role == "super_admin":
        return "enterprise"
    try:
        row = conn.execute(
            "SELECT plan FROM dev_entitlements WHERE user_id = ?",
            (str(user_id),),
        ).fetchone()
        if row and row[0]:
            return str(row[0]).lower()
    except Exception:
        pass
    return "free"


def _row_to_monitored_dict(row: Any) -> Dict[str, Any]:
    return {
        "monitoring_id": row[0],
        "organization_id": row[1],
        "project_id": row[2],
        "user_id": row[3],
        "scan_id": row[4],
        "blockchain": row[5],
        "contract_address": row[6],
        "token_name": row[7],
        "token_symbol": row[8],
        "baseline_price": float(row[9]),
        "baseline_timestamp": row[10],
        "current_price": float(row[11]),
        "highest_observed_price": float(row[12]),
        "current_multiple": float(row[13]),
        "percentage_change": float(row[14]),
        "drawdown_from_high_pct": float(row[15]),
        "market_cap": float(row[16]) if row[16] is not None else None,
        "liquidity_usd": float(row[17]) if row[17] is not None else None,
        "data_source": row[18],
        "data_freshness": row[19],
        "monitoring_status": row[20],
        "positive_thresholds": json.loads(row[21]) if row[21] else [],
        "negative_thresholds": json.loads(row[22]) if row[22] else [],
        "drawdown_threshold_pct": float(row[23]) if row[23] is not None else None,
        "last_checked_at": row[24],
        "last_successful_at": row[25],
        "created_at": row[26],
        "updated_at": row[27],
        "performance_basis": "unrealized_price_since_scan",
    }


def _row_to_alert_dict(row: Any) -> Dict[str, Any]:
    return {
        "alert_id": row[0],
        "monitoring_id": row[1],
        "organization_id": row[2],
        "project_id": row[3],
        "user_id": row[4],
        "blockchain": row[5],
        "contract_address": row[6],
        "token_name": row[7],
        "token_symbol": row[8],
        "alert_type": row[9],
        "threshold_value": float(row[10]),
        "baseline_price": float(row[11]),
        "observed_price": float(row[12]),
        "observed_multiple": float(row[13]),
        "observed_percentage_change": float(row[14]),
        "market_cap": float(row[15]) if row[15] is not None else None,
        "provider": row[16],
        "message": row[17],
        "notification_status": row[18],
        "read_status": bool(row[19]),
        "event_timestamp": row[20],
        "created_at": row[21],
        "performance_basis": "unrealized_price_since_scan",
    }


def build_performance_alerts_router(
    get_current_user: Callable[..., Any],
    require_super_admin: Callable[..., Any],
    get_dev_db: Callable[..., Any],
) -> APIRouter:
    router = APIRouter(tags=["Token Performance Monitoring"])

    @router.post("/api/scanner/monitor")
    async def register_token_for_monitoring(
        payload: MonitorRegisterRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        role = str(current_user.get("role", "project_owner"))
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user identity")

        ca = payload.contract_address.strip()
        chain_check = detect_chain(ca)
        if chain_check == "unknown":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported or invalid contract address")

        market_snapshot = await fetch_dexscreener_market_data(ca)
        if not market_snapshot or not market_snapshot.get("found"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unable to retrieve verified live market data for this contract address",
            )

        with get_dev_db() as conn:
            ensure_performance_schema(conn)
            plan = _get_user_plan(conn, user_id, role)
            try:
                record = register_token_monitoring(
                    user_id=user_id,
                    contract_address=ca,
                    market_snapshot=market_snapshot,
                    user_plan=plan,
                    organization_id=str(current_user.get("organization_id") or user_id),
                    project_id=payload.project_id,
                    scan_id=payload.scan_id,
                    positive_thresholds=payload.positive_thresholds,
                    negative_thresholds=payload.negative_thresholds,
                    drawdown_threshold_pct=payload.drawdown_threshold_pct,
                    conn=conn,
                )
            except PermissionError as exc:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
            except ValueError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        return {"status": "ok", "monitored_token": record}

    @router.get("/api/scanner/monitored")
    async def list_monitored_tokens(
        all_tenants: bool = Query(default=False),
        status_filter: Optional[str] = Query(default=None),
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        role = str(current_user.get("role", "project_owner"))
        if all_tenants and role != "super_admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super Admin role required for global view")

        with get_dev_db() as conn:
            ensure_performance_schema(conn)
            query = """
                SELECT id, organization_id, project_id, user_id, scan_id, blockchain, contract_address,
                       token_name, token_symbol, baseline_price, baseline_timestamp, current_price,
                       highest_observed_price, current_multiple, percentage_change, drawdown_from_high_pct,
                       market_cap, liquidity_usd, data_source, data_freshness, monitoring_status,
                       positive_thresholds_json, negative_thresholds_json, drawdown_threshold_pct,
                       last_checked_at, last_successful_at, created_at, updated_at
                FROM monitored_tokens
                WHERE 1=1
            """
            params: List[Any] = []
            if not (all_tenants and role == "super_admin"):
                query += " AND user_id = ?"
                params.append(user_id)
            if status_filter:
                query += " AND monitoring_status = ?"
                params.append(status_filter)
            query += " ORDER BY updated_at DESC"
            rows = conn.execute(query, params).fetchall()

        return {"items": [_row_to_monitored_dict(r) for r in rows], "count": len(rows)}

    @router.patch("/api/scanner/monitored/{monitoring_id}")
    async def update_monitored_token(
        monitoring_id: str,
        payload: MonitorUpdateRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        role = str(current_user.get("role", "project_owner"))

        with get_dev_db() as conn:
            ensure_performance_schema(conn)
            row = conn.execute(
                "SELECT user_id FROM monitored_tokens WHERE id = ?",
                (monitoring_id,),
            ).fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitored token not found")
            if str(row[0]) != user_id and role != "super_admin":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

            updates: List[str] = []
            params: List[Any] = []
            if payload.monitoring_status is not None:
                if payload.monitoring_status not in ("active", "paused", "stopped"):
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid monitoring_status")
                updates.append("monitoring_status = ?")
                params.append(payload.monitoring_status)
            if payload.positive_thresholds is not None:
                updates.append("positive_thresholds_json = ?")
                params.append(json.dumps(sorted({float(x) for x in payload.positive_thresholds if float(x) > 1.0})))
            if payload.negative_thresholds is not None:
                updates.append("negative_thresholds_json = ?")
                params.append(json.dumps(sorted({-abs(float(x)) for x in payload.negative_thresholds if float(x) != 0})))
            if payload.drawdown_threshold_pct is not None:
                updates.append("drawdown_threshold_pct = ?")
                params.append(float(payload.drawdown_threshold_pct))

            if updates:
                now_iso = datetime.now(timezone.utc).isoformat()
                updates.append("updated_at = ?")
                params.append(now_iso)
                params.append(monitoring_id)
                conn.execute(f"UPDATE monitored_tokens SET {', '.join(updates)} WHERE id = ?", params)
                conn.commit()

            updated = get_monitored_token_by_id(monitoring_id, conn)

        return {"status": "ok", "monitored_token": updated}

    @router.delete("/api/scanner/monitored/{monitoring_id}")
    async def delete_monitored_token(
        monitoring_id: str,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        role = str(current_user.get("role", "project_owner"))

        with get_dev_db() as conn:
            ensure_performance_schema(conn)
            row = conn.execute(
                "SELECT user_id FROM monitored_tokens WHERE id = ?",
                (monitoring_id,),
            ).fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitored token not found")
            if str(row[0]) != user_id and role != "super_admin":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            conn.execute("DELETE FROM monitored_tokens WHERE id = ?", (monitoring_id,))
            conn.commit()

        return {"status": "deleted", "monitoring_id": monitoring_id}

    @router.post("/api/scanner/monitored/check-now")
    async def trigger_manual_monitoring_check(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            ensure_performance_schema(conn)
            alerts = await run_performance_monitoring_cycle(conn=conn, user_id_filter=user_id)
        return {"status": "ok", "new_alerts_count": len(alerts), "new_alerts": alerts}

    @router.get("/api/scanner/performance-alerts")
    async def list_performance_alerts(
        unread_only: bool = Query(default=False),
        blockchain: Optional[str] = Query(default=None),
        alert_type: Optional[str] = Query(default=None),
        token: Optional[str] = Query(default=None),
        all_tenants: bool = Query(default=False),
        limit: int = Query(default=100, ge=1, le=500),
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        role = str(current_user.get("role", "project_owner"))
        if all_tenants and role != "super_admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super Admin role required for global alerts")

        with get_dev_db() as conn:
            ensure_performance_schema(conn)
            query = """
                SELECT id, monitoring_id, organization_id, project_id, user_id, blockchain,
                       contract_address, token_name, token_symbol, alert_type, threshold_value,
                       baseline_price, observed_price, observed_multiple, observed_percentage_change,
                       market_cap, provider, message, notification_status, read_status,
                       event_timestamp, created_at
                FROM token_performance_alerts
                WHERE 1=1
            """
            params: List[Any] = []
            if not (all_tenants and role == "super_admin"):
                query += " AND user_id = ?"
                params.append(user_id)
            if unread_only:
                query += " AND read_status = 0"
            if blockchain:
                query += " AND LOWER(blockchain) = LOWER(?)"
                params.append(blockchain.strip())
            if alert_type:
                query += " AND alert_type = ?"
                params.append(alert_type.strip())
            if token:
                like = f"%{token.strip()}%"
                query += " AND (LOWER(token_symbol) LIKE LOWER(?) OR LOWER(token_name) LIKE LOWER(?) OR LOWER(contract_address) LIKE LOWER(?))"
                params.extend([like, like, like])
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(query, params).fetchall()

            unread_q = "SELECT COUNT(*) FROM token_performance_alerts WHERE read_status = 0"
            unread_params: List[Any] = []
            if not (all_tenants and role == "super_admin"):
                unread_q += " AND user_id = ?"
                unread_params.append(user_id)
            unread_count = int(conn.execute(unread_q, unread_params).fetchone()[0])

        return {
            "alerts": [_row_to_alert_dict(r) for r in rows],
            "unread_count": unread_count,
        }

    @router.post("/api/scanner/performance-alerts/{alert_id}/read")
    async def mark_performance_alert_read(
        alert_id: str,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        role = str(current_user.get("role", "project_owner"))

        with get_dev_db() as conn:
            ensure_performance_schema(conn)
            row = conn.execute(
                "SELECT user_id FROM token_performance_alerts WHERE id = ?",
                (alert_id,),
            ).fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
            if str(row[0]) != user_id and role != "super_admin":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            conn.execute(
                "UPDATE token_performance_alerts SET read_status = 1, notification_status = 'read' WHERE id = ?",
                (alert_id,),
            )
            conn.commit()
        return {"status": "ok", "alert_id": alert_id}

    @router.post("/api/scanner/performance-alerts/read-all")
    async def mark_all_performance_alerts_read(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_id = str(current_user.get("id", ""))
        with get_dev_db() as conn:
            ensure_performance_schema(conn)
            conn.execute(
                "UPDATE token_performance_alerts SET read_status = 1, notification_status = 'read' WHERE user_id = ? AND read_status = 0",
                (user_id,),
            )
            conn.commit()
        return {"status": "ok"}

    @router.get("/api/scanner/performance-alerts/stream")
    async def stream_performance_alerts(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> StreamingResponse:
        user_id = str(current_user.get("id", ""))

        async def event_generator():
            seen_ids: set[str] = set()
            for tick in range(60):  # ~5 minutes per SSE connection before clean reconnect
                try:
                    with get_dev_db() as conn:
                        ensure_performance_schema(conn)
                        rows = conn.execute(
                            """
                            SELECT id, monitoring_id, organization_id, project_id, user_id, blockchain,
                                   contract_address, token_name, token_symbol, alert_type, threshold_value,
                                   baseline_price, observed_price, observed_multiple, observed_percentage_change,
                                   market_cap, provider, message, notification_status, read_status,
                                   event_timestamp, created_at
                            FROM token_performance_alerts
                            WHERE user_id = ? AND read_status = 0
                            ORDER BY created_at DESC LIMIT 20
                            """,
                            (user_id,),
                        ).fetchall()
                    new_events = []
                    for r in rows:
                        if r[0] not in seen_ids:
                            seen_ids.add(r[0])
                            new_events.append(_row_to_alert_dict(r))
                    if new_events:
                        payload = json.dumps({"type": "performance_alerts", "alerts": new_events})
                        yield f"data: {payload}\n\n"
                    elif tick == 0:
                        yield f"data: {json.dumps({'type': 'connected'})}\n\n"
                    else:
                        yield ": keepalive\n\n"
                except Exception as exc:
                    logger.warning("SSE stream query error: %s", exc)
                    yield ": keepalive\n\n"
                await asyncio.sleep(5)

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @router.get("/api/admin/performance-monitoring")
    async def get_admin_performance_monitoring(
        current_user: Dict[str, Any] = Depends(require_super_admin),
    ) -> Dict[str, Any]:
        with get_dev_db() as conn:
            ensure_performance_schema(conn)
            total_monitored = int(conn.execute("SELECT COUNT(*) FROM monitored_tokens").fetchone()[0])
            active_monitored = int(
                conn.execute("SELECT COUNT(*) FROM monitored_tokens WHERE monitoring_status = 'active'").fetchone()[0]
            )
            stale_or_failed = int(
                conn.execute(
                    "SELECT COUNT(*) FROM monitored_tokens WHERE data_freshness != 'live' AND monitoring_status = 'active'"
                ).fetchone()[0]
            )
            positive_alerts = int(
                conn.execute(
                    "SELECT COUNT(*) FROM token_performance_alerts WHERE alert_type = 'positive_milestone'"
                ).fetchone()[0]
            )
            negative_alerts = int(
                conn.execute(
                    "SELECT COUNT(*) FROM token_performance_alerts WHERE alert_type IN ('negative_decline', 'drawdown_alert')"
                ).fetchone()[0]
            )
            top_milestones_rows = conn.execute(
                """
                SELECT alert_type, threshold_value, COUNT(*) AS cnt
                FROM token_performance_alerts
                GROUP BY alert_type, threshold_value
                ORDER BY cnt DESC LIMIT 10
                """
            ).fetchall()
            recent_alerts_rows = conn.execute(
                """
                SELECT id, monitoring_id, organization_id, project_id, user_id, blockchain,
                       contract_address, token_name, token_symbol, alert_type, threshold_value,
                       baseline_price, observed_price, observed_multiple, observed_percentage_change,
                       market_cap, provider, message, notification_status, read_status,
                       event_timestamp, created_at
                FROM token_performance_alerts
                ORDER BY created_at DESC LIMIT 25
                """
            ).fetchall()
            monitored_rows = conn.execute(
                """
                SELECT id, organization_id, project_id, user_id, scan_id, blockchain, contract_address,
                       token_name, token_symbol, baseline_price, baseline_timestamp, current_price,
                       highest_observed_price, current_multiple, percentage_change, drawdown_from_high_pct,
                       market_cap, liquidity_usd, data_source, data_freshness, monitoring_status,
                       positive_thresholds_json, negative_thresholds_json, drawdown_threshold_pct,
                       last_checked_at, last_successful_at, created_at, updated_at
                FROM monitored_tokens
                ORDER BY updated_at DESC LIMIT 50
                """
            ).fetchall()
            settings = get_platform_monitoring_settings(conn)

        return {
            "summary": {
                "total_monitored_tokens": total_monitored,
                "active_monitored_tokens": active_monitored,
                "stale_or_provider_warning_count": stale_or_failed,
                "total_positive_alerts": positive_alerts,
                "total_negative_alerts": negative_alerts,
                "provider_health": "degraded" if stale_or_failed > 0 else "healthy",
            },
            "top_milestones": [
                {"alert_type": r[0], "threshold_value": float(r[1]), "count": int(r[2])}
                for r in top_milestones_rows
            ],
            "recent_alerts": [_row_to_alert_dict(r) for r in recent_alerts_rows],
            "monitored_tokens": [_row_to_monitored_dict(r) for r in monitored_rows],
            "settings": settings,
            "audited_by": current_user.get("email") or current_user.get("id"),
        }

    @router.post("/api/admin/performance-monitoring/settings")
    async def update_admin_performance_settings(
        payload: AdminMonitorSettingsRequest,
        current_user: Dict[str, Any] = Depends(require_super_admin),
    ) -> Dict[str, Any]:
        with get_dev_db() as conn:
            ensure_performance_schema(conn)
            current = get_platform_monitoring_settings(conn)
            pos = (
                sorted({float(x) for x in payload.default_positive_thresholds if float(x) > 1.0})
                if payload.default_positive_thresholds is not None
                else current["default_positive_thresholds"]
            )
            neg = (
                sorted({-abs(float(x)) for x in payload.default_negative_thresholds if float(x) != 0})
                if payload.default_negative_thresholds is not None
                else current["default_negative_thresholds"]
            )
            max_free = payload.max_monitored_free if payload.max_monitored_free is not None else current["max_monitored_free"]
            max_pro = payload.max_monitored_pro if payload.max_monitored_pro is not None else current["max_monitored_pro"]
            poll = payload.polling_interval_seconds if payload.polling_interval_seconds is not None else current["polling_interval_seconds"]
            now_iso = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                UPDATE performance_monitor_settings
                SET default_positive_thresholds_json = ?,
                    default_negative_thresholds_json = ?,
                    max_monitored_free = ?,
                    max_monitored_pro = ?,
                    polling_interval_seconds = ?,
                    updated_at = ?
                WHERE id = 'global'
                """,
                (json.dumps(pos), json.dumps(neg), max_free, max_pro, poll, now_iso),
            )
            conn.commit()
            updated = get_platform_monitoring_settings(conn)

        logger.info("Super Admin %s updated global performance monitoring settings", current_user.get("id"))
        return {"status": "ok", "settings": updated}

    return router
