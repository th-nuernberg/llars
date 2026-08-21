"""
Pipeline Orchestrator Service.

Central controller for the automated LLM evaluation pipeline.
Manages the loop: Prompt Generation -> Batch Generation -> LLM Evaluation -> Analysis.
Delegates to existing services (BatchGenerationService, OutputExportService, etc.).
"""

import logging
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from db import db
from db.models.pipeline import (
    PipelineIteration,
    PipelineIterationPhase,
    PipelineIterationStatus,
    PipelineRun,
    PipelineStatus,
)
from decorators.error_handler import NotFoundError, ValidationError

logger = logging.getLogger(__name__)

# Active run threads — keyed by run_id
_active_threads: Dict[int, threading.Event] = {}


class PipelineOrchestratorService:
    """Orchestrates the automated pipeline loop."""

    # =========================================================================
    # CRUD
    # =========================================================================

    @classmethod
    def create_run(
        cls,
        name: str,
        config: Dict[str, Any],
        candidate_models: List[str],
        created_by: str,
        *,
        description: Optional[str] = None,
        scenario_type: str = 'greenfield',
        reference_model_id: Optional[str] = None,
        source_scenario_id: Optional[int] = None,
        max_iterations: int = 10,
        budget_tokens_total: int = 500000,
    ) -> PipelineRun:
        """Create a new pipeline run."""
        run = PipelineRun(
            name=name,
            description=description,
            config_json=config,
            scenario_type=scenario_type,
            reference_model_id=reference_model_id,
            candidate_models=candidate_models,
            source_scenario_id=source_scenario_id,
            max_iterations=max_iterations,
            budget_tokens_total=budget_tokens_total,
            created_by=created_by,
        )
        db.session.add(run)
        db.session.commit()

        logger.info("[Pipeline] Created run %d: %s", run.id, name)
        return run

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    @classmethod
    def start_run(cls, run_id: int) -> PipelineRun:
        """Start or resume a pipeline run in a background thread."""
        run = PipelineRun.query.get(run_id)
        if not run:
            raise NotFoundError(f'Pipeline run {run_id} not found')
        if not run.can_start:
            raise ValidationError(
                f"Cannot start run in status '{run.status.value}'"
            )

        run.status = PipelineStatus.RUNNING
        if not run.started_at:
            run.started_at = datetime.utcnow()
        db.session.commit()

        # Emit run started event
        cls._emit_event(run_id, 'pipeline:run:started', {
            'run_id': run_id,
            'config': run.config_json,
        })

        # Create stop event and spawn background thread
        stop_event = threading.Event()
        _active_threads[run_id] = stop_event

        def _run():
            try:
                from main import app
                with app.app_context():
                    cls._run_loop(run_id, stop_event)
            except Exception as e:
                logger.exception("[Pipeline] Run %d failed: %s", run_id, e)
                try:
                    from main import app
                    with app.app_context():
                        cls._mark_run_failed(run_id, str(e))
                except Exception:
                    logger.exception("[Pipeline] Could not mark run %d as failed", run_id)
            finally:
                _active_threads.pop(run_id, None)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        logger.info("[Pipeline] Started run %d in background thread", run_id)
        return run

    @classmethod
    def pause_run(cls, run_id: int) -> PipelineRun:
        """Pause a running pipeline."""
        run = PipelineRun.query.get(run_id)
        if not run:
            raise NotFoundError(f'Pipeline run {run_id} not found')
        if not run.can_pause:
            raise ValidationError(
                f"Cannot pause run in status '{run.status.value}'"
            )

        run.status = PipelineStatus.PAUSED
        db.session.commit()

        # Signal the background thread to stop
        stop_event = _active_threads.get(run_id)
        if stop_event:
            stop_event.set()

        cls._emit_event(run_id, 'pipeline:run:paused', {'run_id': run_id})
        logger.info("[Pipeline] Paused run %d", run_id)
        return run

    @classmethod
    def cancel_run(cls, run_id: int) -> PipelineRun:
        """Cancel a pipeline run."""
        run = PipelineRun.query.get(run_id)
        if not run:
            raise NotFoundError(f'Pipeline run {run_id} not found')
        if not run.can_cancel:
            raise ValidationError(
                f"Cannot cancel run in status '{run.status.value}'"
            )

        run.status = PipelineStatus.CANCELLED
        run.completed_at = datetime.utcnow()
        db.session.commit()

        stop_event = _active_threads.get(run_id)
        if stop_event:
            stop_event.set()

        cls._emit_event(run_id, 'pipeline:run:completed', {
            'run_id': run_id,
            'status': 'cancelled',
        })
        logger.info("[Pipeline] Cancelled run %d", run_id)
        return run

    @classmethod
    def handle_review(cls, run_id: int, decision: str) -> PipelineRun:
        """Handle human review decision."""
        run = PipelineRun.query.get(run_id)
        if not run:
            raise NotFoundError(f'Pipeline run {run_id} not found')
        if run.status != PipelineStatus.WAITING_FOR_REVIEW:
            raise ValidationError("Run is not waiting for review")

        if decision == 'deploy':
            run.status = PipelineStatus.COMPLETED
            run.completed_at = datetime.utcnow()
            db.session.commit()
            cls._emit_event(run_id, 'pipeline:run:completed', {
                'run_id': run_id,
                'best_config': run.best_config_json,
                'total_iterations': run.current_iteration,
            })
        elif decision == 'reject':
            run.status = PipelineStatus.CANCELLED
            run.completed_at = datetime.utcnow()
            db.session.commit()
            cls._emit_event(run_id, 'pipeline:run:completed', {
                'run_id': run_id,
                'status': 'rejected',
            })
        elif decision == 'continue':
            # Resume the loop
            cls.start_run(run_id)

        logger.info("[Pipeline] Review for run %d: %s", run_id, decision)
        return run

    # =========================================================================
    # CORE LOOP
    # =========================================================================

    @classmethod
    def _run_loop(cls, run_id: int, stop_event: threading.Event) -> None:
        """
        Main pipeline loop. Runs in background thread.

        Each iteration:
        1. Generate prompt variants (via PromptAgentService)
        2. Run batch generation (via BatchGenerationService)
        3. Export to evaluation scenario + run LLM eval
        4. Analyze scores and decide: continue / converged / escalate
        """
        from services.pipeline.prompt_agent_service import PromptAgentService
        from services.pipeline.convergence_service import ConvergenceService

        run = PipelineRun.query.get(run_id)
        if not run:
            return

        history = []

        while run.current_iteration < run.max_iterations:
            # Check for stop signal
            if stop_event.is_set():
                logger.info("[Pipeline] Run %d stopped by signal", run_id)
                return

            # Re-read run status (could have been paused/cancelled externally)
            db.session.refresh(run)
            if run.status != PipelineStatus.RUNNING:
                logger.info("[Pipeline] Run %d no longer running: %s", run_id, run.status.value)
                return

            # Budget check
            if run.budget_tokens_used >= run.budget_tokens_total:
                logger.info("[Pipeline] Run %d budget exhausted", run_id)
                run.status = PipelineStatus.WAITING_FOR_REVIEW
                db.session.commit()
                cls._emit_event(run_id, 'pipeline:run:waiting_for_review', {
                    'run_id': run_id,
                    'reason': 'budget_exhausted',
                    'best_config': run.best_config_json,
                })
                return

            run.current_iteration += 1
            iteration_num = run.current_iteration
            db.session.commit()

            logger.info("[Pipeline] Run %d starting iteration %d", run_id, iteration_num)

            # Create iteration record
            iteration = PipelineIteration(
                run_id=run_id,
                iteration_number=iteration_num,
                phase=PipelineIterationPhase.PROMPT_GENERATION,
                status=PipelineIterationStatus.RUNNING,
            )
            db.session.add(iteration)
            db.session.commit()

            cls._emit_event(run_id, 'pipeline:iteration:started', {
                'run_id': run_id,
                'iteration': iteration_num,
                'phase': 'prompt_generation',
            })

            try:
                # Phase 1: Generate prompt variants
                cls._update_phase(iteration, PipelineIterationPhase.PROMPT_GENERATION, run_id)
                prompt_variants = PromptAgentService.generate_variants(run, history)
                iteration.prompt_variants_json = [pv for pv in prompt_variants]
                db.session.commit()

                if stop_event.is_set():
                    return

                # Phase 2: Batch generation
                cls._update_phase(iteration, PipelineIterationPhase.BATCH_GENERATION, run_id)
                generation_job_id = cls._run_batch_generation(run, prompt_variants)
                iteration.generation_job_id = generation_job_id
                db.session.commit()

                # Wait for generation to complete
                gen_result = cls._wait_for_generation(generation_job_id, stop_event)
                if gen_result is None:
                    return  # Stopped

                if stop_event.is_set():
                    return

                # Phase 3: Evaluation
                cls._update_phase(iteration, PipelineIterationPhase.EVALUATION, run_id)
                eval_scenario_id = cls._run_evaluation(run, generation_job_id)
                iteration.eval_scenario_id = eval_scenario_id
                db.session.commit()

                if stop_event.is_set():
                    return

                # Phase 4: Analysis
                cls._update_phase(iteration, PipelineIterationPhase.ANALYSIS, run_id)
                scores = cls._collect_scores(eval_scenario_id, run)
                iteration.scores_json = scores

                # Update token usage
                tokens = gen_result.get('total_tokens', 0)
                iteration.tokens_used = tokens
                run.budget_tokens_used += tokens
                db.session.commit()

                # Run convergence analysis
                decision = ConvergenceService.analyze(
                    current_scores=scores,
                    history=history,
                    thresholds=run.config_json.get('thresholds', {}),
                    max_plateau_iterations=run.config_json.get('max_plateau_iterations', 3),
                )

                iteration.agent_reasoning = decision.get('reasoning', '')
                iteration.delta_to_best = decision.get('delta', 0.0)

                # Update best config if improved
                if decision.get('is_new_best', False):
                    run.best_config_json = {
                        'iteration': iteration_num,
                        'scores': scores,
                        'prompt_variants': iteration.prompt_variants_json,
                        'avg_score': decision.get('avg_score', 0),
                    }

                iteration.status = PipelineIterationStatus.COMPLETED
                iteration.completed_at = datetime.utcnow()
                db.session.commit()

                # Add to history for next iteration
                history.append({
                    'iteration': iteration_num,
                    'scores': scores,
                    'reasoning': decision.get('reasoning', ''),
                    'prompt_variants': iteration.prompt_variants_json,
                })

                # Emit iteration completed
                cls._emit_event(run_id, 'pipeline:iteration:completed', {
                    'run_id': run_id,
                    'iteration': iteration_num,
                    'scores': scores,
                    'reasoning': decision.get('reasoning', ''),
                    'delta': decision.get('delta', 0.0),
                    'best_so_far': run.best_config_json,
                })

                # Decision
                if decision['action'] == 'converged':
                    run.status = PipelineStatus.COMPLETED
                    run.completed_at = datetime.utcnow()
                    db.session.commit()
                    cls._emit_event(run_id, 'pipeline:run:completed', {
                        'run_id': run_id,
                        'best_config': run.best_config_json,
                        'total_iterations': run.current_iteration,
                    })
                    logger.info("[Pipeline] Run %d converged at iteration %d", run_id, iteration_num)
                    return

                elif decision['action'] == 'escalate':
                    run.status = PipelineStatus.WAITING_FOR_REVIEW
                    db.session.commit()
                    cls._emit_event(run_id, 'pipeline:run:waiting_for_review', {
                        'run_id': run_id,
                        'reason': decision.get('reason', 'plateau'),
                        'best_config': run.best_config_json,
                    })
                    logger.info("[Pipeline] Run %d escalated for review at iteration %d", run_id, iteration_num)
                    return

                # else: continue to next iteration

            except Exception as e:
                logger.exception(
                    "[Pipeline] Run %d iteration %d failed: %s",
                    run_id, iteration_num, e
                )
                iteration.status = PipelineIterationStatus.FAILED
                iteration.agent_reasoning = f"Error: {str(e)}"
                iteration.completed_at = datetime.utcnow()
                db.session.commit()

                cls._emit_event(run_id, 'pipeline:iteration:completed', {
                    'run_id': run_id,
                    'iteration': iteration_num,
                    'status': 'failed',
                    'error': str(e),
                })

                # Continue to next iteration despite failure
                continue

        # Max iterations reached
        run.status = PipelineStatus.WAITING_FOR_REVIEW
        db.session.commit()
        cls._emit_event(run_id, 'pipeline:run:waiting_for_review', {
            'run_id': run_id,
            'reason': 'max_iterations',
            'best_config': run.best_config_json,
        })
        logger.info("[Pipeline] Run %d reached max iterations", run_id)

    # =========================================================================
    # PHASE HELPERS
    # =========================================================================

    @classmethod
    def _update_phase(
        cls,
        iteration: PipelineIteration,
        phase: PipelineIterationPhase,
        run_id: int,
    ) -> None:
        """Update iteration phase and emit event."""
        iteration.phase = phase
        db.session.commit()

        cls._emit_event(run_id, 'pipeline:iteration:phase_changed', {
            'run_id': run_id,
            'iteration': iteration.iteration_number,
            'phase': phase.value,
        })

    @classmethod
    def _run_batch_generation(
        cls,
        run: PipelineRun,
        prompt_variants: List[Dict[str, Any]],
    ) -> int:
        """Create and start a batch generation job. Returns job ID."""
        from services.generation import BatchGenerationService

        config = run.config_json or {}

        # Build generation job config
        job_config = {
            'mode': 'matrix',
            'sources': config.get('sources', {
                'type': 'scenario',
                'scenario_id': run.source_scenario_id,
            }),
            'prompts': prompt_variants,
            'llm_models': run.candidate_models,
            'generation_params': config.get('generation_params', {
                'temperature': 0.7,
                'max_tokens': None,
            }),
        }

        job = BatchGenerationService.create_job(
            name=f"Pipeline {run.id} Iter {run.current_iteration}",
            config=job_config,
            created_by=run.created_by,
            description=f"Auto-generated by pipeline run {run.id}",
        )

        BatchGenerationService.start_job(job.id)

        logger.info("[Pipeline] Created generation job %d for run %d", job.id, run.id)
        return job.id

    @classmethod
    def _wait_for_generation(
        cls,
        job_id: int,
        stop_event: threading.Event,
        timeout: float = 3600,
        poll_interval: float = 2.0,
    ) -> Optional[Dict[str, Any]]:
        """Poll for generation job completion. Returns status dict or None if stopped."""
        from services.generation import BatchGenerationService

        start_time = time.time()

        while time.time() - start_time < timeout:
            if stop_event.is_set():
                return None

            status = BatchGenerationService.get_job_status(job_id)
            job_status = status.get('status', '')

            if job_status == 'completed':
                return status
            elif job_status in ('failed', 'cancelled'):
                raise RuntimeError(
                    f"Generation job {job_id} {job_status}: "
                    f"{status.get('error', 'Unknown error')}"
                )

            time.sleep(poll_interval)

        raise TimeoutError(f"Generation job {job_id} timed out after {timeout}s")

    @classmethod
    def _run_evaluation(cls, run: PipelineRun, generation_job_id: int) -> int:
        """Export generation outputs to scenario and run LLM evaluation. Returns scenario ID."""
        from services.generation.output_export_service import OutputExportService
        from services.llm.llm_ai_task_runner import LLMAITaskRunner

        config = run.config_json or {}
        eval_type = config.get('evaluation_type', 'rating')
        eval_model = config.get('eval_model_id')

        # Create evaluation scenario from generation outputs
        scenario = OutputExportService.create_evaluation_scenario_fixed(
            job_id=generation_job_id,
            scenario_name=f"Pipeline {run.id} Eval Iter {run.current_iteration}",
            evaluation_type=eval_type,
            created_by=run.created_by,
            config_json=config.get('eval_config'),
        )

        logger.info(
            "[Pipeline] Created eval scenario %d from job %d",
            scenario.id, generation_job_id,
        )

        # Run LLM evaluation synchronously
        model_ids = [eval_model] if eval_model else None
        LLMAITaskRunner.run_for_scenario(
            scenario_id=scenario.id,
            model_ids=model_ids,
        )

        logger.info("[Pipeline] LLM evaluation completed for scenario %d", scenario.id)
        return scenario.id

    @classmethod
    def _collect_scores(cls, scenario_id: int, run: PipelineRun) -> Dict[str, Any]:
        """Collect evaluation scores from the completed scenario."""
        from db.models.scenario import ItemDimensionRating, RatingScenarios

        scenario = RatingScenarios.query.get(scenario_id)
        if not scenario:
            return {}

        # Get all dimension ratings for this scenario
        ratings = ItemDimensionRating.query.filter_by(
            scenario_id=scenario_id,
        ).all()

        if not ratings:
            return {'dimensions': {}, 'avg_score': 0}

        # Aggregate scores by dimension
        dimension_scores: Dict[str, List[float]] = {}
        for r in ratings:
            dim_id = r.dimension_id or 'overall'
            if dim_id not in dimension_scores:
                dimension_scores[dim_id] = []
            dimension_scores[dim_id].append(float(r.score))

        # Calculate averages
        dimension_avgs = {}
        for dim_id, scores in dimension_scores.items():
            dimension_avgs[dim_id] = round(sum(scores) / len(scores), 2)

        all_scores = [s for scores in dimension_scores.values() for s in scores]
        avg_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0

        return {
            'dimensions': dimension_avgs,
            'avg_score': avg_score,
            'total_ratings': len(ratings),
        }

    # =========================================================================
    # ERROR HANDLING
    # =========================================================================

    @classmethod
    def _mark_run_failed(cls, run_id: int, error: str) -> None:
        """Mark a run as failed."""
        run = PipelineRun.query.get(run_id)
        if run:
            run.status = PipelineStatus.FAILED
            run.error_message = error
            run.completed_at = datetime.utcnow()
            db.session.commit()

        cls._emit_event(run_id, 'pipeline:run:failed', {
            'run_id': run_id,
            'error': error,
        })

    # =========================================================================
    # SOCKET.IO
    # =========================================================================

    @classmethod
    def _emit_event(cls, run_id: int, event: str, data: Dict[str, Any]) -> None:
        """Emit a Socket.IO event to the pipeline room."""
        try:
            from main import socketio
            room = f"pipeline_run_{run_id}"
            socketio.emit(event, data, room=room)
        except ImportError:
            logger.debug("[Pipeline] SocketIO not available")
        except Exception as e:
            logger.debug("[Pipeline] Could not emit event: %s", e)
