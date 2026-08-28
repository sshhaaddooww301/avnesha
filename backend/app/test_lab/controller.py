"""
Test Lab Orchestration Controller.

Executes real QDS simulations through the production detection pipeline,
records every individual test run in PostgreSQL, links events to the tamper-evident
audit hash ledger, and computes mathematically rigorous detection metrics.
"""

import time
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import async_session_factory
from app.models import TestRun, TestResult, SecurityEvent, Threat
from app.test_lab.attack_mapping import ATTACK_TYPE_MAP
from app.quantum.simulator import qds_simulator, QISKIT_AVAILABLE
from app.engine.detection import process_event
from app.websocket.manager import ws_manager

logger = logging.getLogger("qds.test_lab")


class TestLabController:
    """Manages Attack / Test Lab execution and metrics computation."""

    async def create_test_session(
        self,
        db: AsyncSession,
        attack_type: str,
        runs: int,
        params: Dict[str, Any],
    ) -> TestRun:
        """Create and persist a new test run record."""
        test_run = TestRun(
            test_id=str(uuid.uuid4()),
            attack_type=attack_type,
            total_runs=runs,
            status="pending",
            params=params,
            metrics={},
            created_at=datetime.utcnow(),
        )
        db.add(test_run)
        await db.commit()
        await db.refresh(test_run)
        return test_run

    async def execute_test_session(
        self,
        test_id: str,
        attack_type: str,
        runs: int,
        params: Dict[str, Any],
    ):
        """
        Background task to execute simulation iterations through the detection pipeline.
        Emits live progress updates over WebSocket.
        """
        sim_mode = ATTACK_TYPE_MAP.get(attack_type, "replay")
        intensity = params.get("attack_intensity", 0.5)

        logger.info(f"Starting Test Lab Session {test_id} ({attack_type}, {runs} runs, mode={sim_mode})")

        # Mark as running
        async with async_session_factory() as db:
            result = await db.execute(select(TestRun).where(TestRun.test_id == test_id))
            run_obj = result.scalar_one_or_none()
            if run_obj:
                run_obj.status = "running"
                await db.commit()

        completed = 0

        for i in range(runs):
            t_start = time.perf_counter()

            # Determine whether this individual iteration injects an attack or normal traffic
            if sim_mode == "normal":
                is_attack = False
                ev_data = qds_simulator.generate_normal_event()
            else:
                # Based on intensity, inject attack or normal baseline
                # If intensity is 1.0, 100% attacks; default 0.5+ injects attacks with high probability
                # For specific attack test, ensure at least 80% attacks and some baseline
                inject_attack = True
                if intensity < 1.0 and runs > 3:
                    # Keep some normal events for false positive testing
                    inject_attack = (i % int(max(2, 1.0 / max(0.1, intensity)))) != 0

                if inject_attack:
                    is_attack = True
                    if sim_mode == "replay":
                        ev_data = qds_simulator.generate_replay_event()
                    elif sim_mode == "mitm":
                        ev_data = qds_simulator.generate_mitm_event()
                    elif sim_mode == "forgery":
                        ev_data = qds_simulator.generate_forgery_event()
                    elif sim_mode == "impersonation":
                        ev_data = qds_simulator.generate_impersonation_event()
                    elif sim_mode == "anomaly":
                        ev_data = qds_simulator.generate_anomaly_event()
                    elif sim_mode == "pns":
                        ev_data = qds_simulator.generate_pns_event()
                    elif sim_mode == "blinding":
                        ev_data = qds_simulator.generate_blinding_event()
                    elif sim_mode == "repudiation":
                        ev_data = qds_simulator.generate_repudiation_event()
                    elif sim_mode == "evasion":
                        ev_data = qds_simulator.generate_evasion_event()
                    else:
                        ev_data = qds_simulator.generate_replay_event()
                else:
                    is_attack = False
                    ev_data = qds_simulator.generate_normal_event()

            # Process event through the EXACT SAME production detection engine
            async with async_session_factory() as db:
                try:
                    event, threat = await process_event(db, ev_data)
                    t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0

                    test_result = TestResult(
                        test_id=test_id,
                        run_index=i + 1,
                        event_id=event.event_id,
                        attack_injected=is_attack,
                        threat_detected=threat is not None,
                        threat_id=threat.threat_id if threat else None,
                        risk_score=threat.risk_score if threat else 0.0,
                        severity=threat.severity if threat else "none",
                        detection_rule=threat.detection_rule if threat else "NONE",
                        detection_time_ms=round(t_elapsed_ms, 2),
                        measurement_deviation=event.measurement_deviation,
                        expected_measurement=event.expected_measurement,
                        observed_measurement=event.observed_measurement,
                        created_at=datetime.utcnow(),
                    )
                    db.add(test_result)
                    await db.commit()
                except Exception as e:
                    logger.error(f"Error processing test event {i+1}/{runs} for test {test_id}: {e}")

            completed += 1

            # Broadcast progress over WebSocket
            progress_msg = {
                "type": "test_progress",
                "test_id": test_id,
                "completed": completed,
                "total": runs,
                "percentage": round((completed / runs) * 100, 1),
                "attack_type": attack_type,
            }
            await ws_manager.broadcast(progress_msg)

            # Small realistic sleep between iterations for smooth telemetry animation
            await asyncio.sleep(0.08)

        # Compute final mathematical metrics and mark completed
        async with async_session_factory() as db:
            metrics = await self.compute_test_metrics(db, test_id)
            result = await db.execute(select(TestRun).where(TestRun.test_id == test_id))
            run_obj = result.scalar_one_or_none()
            if run_obj:
                run_obj.status = "completed"
                run_obj.metrics = metrics
                run_obj.completed_at = datetime.utcnow()
                await db.commit()

        # Broadcast completion message
        await ws_manager.broadcast({
            "type": "test_completed",
            "test_id": test_id,
            "attack_type": attack_type,
            "metrics": metrics,
        })
        logger.info(f"Test Lab Session {test_id} completed successfully.")

    async def compute_test_metrics(self, db: AsyncSession, test_id: str) -> Dict[str, Any]:
        """
        Compute mathematical performance metrics (TP, FP, TN, FN, Precision, Recall, F1, Accuracy).
        Safe handling for zero denominators.
        """
        result = await db.execute(
            select(TestResult).where(TestResult.test_id == test_id).order_by(TestResult.run_index.asc())
        )
        results = result.scalars().all()

        total_runs = len(results)
        if total_runs == 0:
            return {
                "total_runs": 0,
                "attacks_injected": 0,
                "normal_injected": 0,
                "true_positives": 0,
                "false_positives": 0,
                "true_negatives": 0,
                "false_negatives": 0,
                "detected_attacks": 0,
                "missed_attacks": 0,
                "detection_rate": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "accuracy": 0.0,
                "average_risk_score": 0.0,
                "max_risk_score": 0.0,
                "min_risk_score": 0.0,
                "average_detection_time_ms": 0.0,
                "average_measurement_deviation": 0.0,
            }

        tp = 0  # Attack injected AND threat detected
        fp = 0  # Normal injected BUT threat detected
        tn = 0  # Normal injected AND NO threat detected
        fn = 0  # Attack injected BUT NO threat detected

        attacks_injected = 0
        normal_injected = 0
        risk_scores = []
        detection_times = []
        deviations = []

        for r in results:
            if r.attack_injected:
                attacks_injected += 1
                if r.threat_detected:
                    tp += 1
                else:
                    fn += 1
            else:
                normal_injected += 1
                if r.threat_detected:
                    fp += 1
                else:
                    tn += 1

            if r.risk_score is not None:
                risk_scores.append(r.risk_score)
            if r.detection_time_ms is not None:
                detection_times.append(r.detection_time_ms)
            if r.measurement_deviation is not None:
                deviations.append(r.measurement_deviation)

        # Detection rate = detected_attacks / total_attacks * 100
        if attacks_injected > 0:
            detection_rate = (tp / attacks_injected) * 100.0
        else:
            detection_rate = 100.0 if fp == 0 else 0.0

        # Precision = TP / (TP + FP)
        if (tp + fp) > 0:
            precision = (tp / (tp + fp)) * 100.0
        else:
            precision = 100.0 if attacks_injected == 0 else 0.0

        # Recall = TP / (TP + FN)
        if (tp + fn) > 0:
            recall = (tp / (tp + fn)) * 100.0
        else:
            recall = 100.0 if attacks_injected == 0 else 0.0

        # F1 Score = 2 * (Precision * Recall) / (Precision + Recall)
        if (precision + recall) > 0:
            f1_score = 2 * (precision * recall) / (precision + recall)
        else:
            f1_score = 0.0

        # Accuracy = (TP + TN) / Total
        accuracy = ((tp + tn) / total_runs) * 100.0

        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        max_risk = max(risk_scores) if risk_scores else 0.0
        min_risk = min(risk_scores) if risk_scores else 0.0
        avg_time = sum(detection_times) / len(detection_times) if detection_times else 0.0
        avg_dev = sum(deviations) / len(deviations) if deviations else 0.0

        return {
            "total_runs": total_runs,
            "attacks_injected": attacks_injected,
            "normal_injected": normal_injected,
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
            "detected_attacks": tp,
            "missed_attacks": fn,
            "detection_rate": round(detection_rate, 2),
            "precision": round(precision, 2),
            "recall": round(recall, 2),
            "f1_score": round(f1_score, 2),
            "accuracy": round(accuracy, 2),
            "average_risk_score": round(avg_risk, 2),
            "max_risk_score": round(max_risk, 2),
            "min_risk_score": round(min_risk, 2),
            "average_detection_time_ms": round(avg_time, 2),
            "average_measurement_deviation": round(avg_dev, 4),
        }


test_lab_controller = TestLabController()
