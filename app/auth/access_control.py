"""
Zentrale Access-Control-Helpers für Resource-Ownership-Prüfungen.

Verhindert IDOR-Schwachstellen, indem bei jedem Zugriff auf eine Resource
geprüft wird, ob der anfragende User berechtigt ist.

Admins haben immer Zugriff (Bypass).

Usage:
    from auth.access_control import require_scenario_membership

    @evaluation_bp.get('/<int:scenario_id>/data')
    @authentik_required
    @handle_api_errors(logger_name='evaluation')
    def get_data(scenario_id):
        require_scenario_membership(scenario_id, g.authentik_user)
        ...
"""

from decorators.error_handler import ForbiddenError, NotFoundError


def require_scenario_membership(scenario_id: int, user) -> None:
    """
    Prüft ob der User Mitglied des Szenarios ist.

    Zugriff haben:
    - Admins (Bypass)
    - Szenario-Ersteller (created_by)
    - ScenarioUsers-Eintrag (OWNER, EVALUATOR, VIEWER)

    Args:
        scenario_id: Szenario-ID
        user: User-Objekt aus g.authentik_user

    Raises:
        ForbiddenError: User hat keinen Zugriff
    """
    from decorators.permission_decorator import has_role
    if has_role(user, 'admin'):
        return

    from db.models import RatingScenarios, ScenarioUsers

    username = getattr(user, 'username', str(user))
    user_id = getattr(user, 'id', None)

    scenario = RatingScenarios.query.get(scenario_id)
    if scenario and scenario.created_by == username:
        return

    if user_id:
        membership = ScenarioUsers.query.filter_by(
            scenario_id=scenario_id,
            user_id=user_id
        ).first()
        if membership:
            return

    raise ForbiddenError('You are not a member of this scenario')


def require_generation_job_owner(job_id: int, user) -> None:
    """
    Prüft ob der User Eigentümer des Generation Jobs ist.

    Zugriff haben:
    - Admins (Bypass)
    - Job-Ersteller (created_by == username)

    Args:
        job_id: GenerationJob-ID
        user: User-Objekt aus g.authentik_user

    Raises:
        ForbiddenError: User ist nicht der Eigentümer
        NotFoundError: Job existiert nicht
    """
    from decorators.permission_decorator import has_role
    if has_role(user, 'admin'):
        return

    from db.models import GenerationJob

    username = getattr(user, 'username', str(user))

    job = GenerationJob.query.get(job_id)
    if not job:
        raise NotFoundError(f'Job {job_id} not found')

    if job.created_by == username:
        return

    raise ForbiddenError('You do not have access to this job')


def require_generation_job_access(job_id: int, user) -> None:
    """
    Prüft ob der User Zugriff auf den Generation Job hat (Owner ODER Shared).

    Zugriff haben:
    - Admins (Bypass)
    - Job-Ersteller (created_by == username)
    - User mit GenerationJobShare-Eintrag (Read-Only)

    Args:
        job_id: GenerationJob-ID
        user: User-Objekt aus g.authentik_user

    Raises:
        ForbiddenError: User hat keinen Zugriff
        NotFoundError: Job existiert nicht
    """
    from decorators.permission_decorator import has_role
    if has_role(user, 'admin'):
        return

    from db.models import GenerationJob, GenerationJobShare

    username = getattr(user, 'username', str(user))
    user_id = getattr(user, 'id', None)

    job = GenerationJob.query.get(job_id)
    if not job:
        raise NotFoundError(f'Job {job_id} not found')

    if job.created_by == username:
        return

    # Check if job is shared with this user
    if user_id:
        share = GenerationJobShare.query.filter_by(
            job_id=job_id,
            shared_with_user_id=user_id
        ).first()
        if share:
            return

    raise ForbiddenError('You do not have access to this job')


def require_judge_session_owner(session_id: int, user) -> None:
    """
    Prüft ob der User Eigentümer der Judge Session ist.

    Zugriff haben:
    - Admins (Bypass)
    - Session-Ersteller (user_id == username)

    Args:
        session_id: JudgeSession-ID
        user: User-Objekt aus g.authentik_user

    Raises:
        ForbiddenError: User ist nicht der Eigentümer
        NotFoundError: Session existiert nicht
    """
    from decorators.permission_decorator import has_role
    if has_role(user, 'admin'):
        return

    from db.tables import JudgeSession

    username = getattr(user, 'username', str(user))

    session = JudgeSession.query.get(session_id)
    if not session:
        raise NotFoundError(f'Session {session_id} not found')

    if session.user_id == username:
        return

    raise ForbiddenError('You do not have access to this session')


def require_pipeline_run_owner(run_id: int, user) -> None:
    """
    Prüft ob der User Eigentümer des Pipeline Runs ist.

    Zugriff haben:
    - Admins (Bypass)
    - Run-Ersteller (created_by == username)

    Args:
        run_id: PipelineRun-ID
        user: User-Objekt aus g.authentik_user

    Raises:
        ForbiddenError: User ist nicht der Eigentümer
        NotFoundError: Run existiert nicht
    """
    from decorators.permission_decorator import has_role
    if has_role(user, 'admin'):
        return

    from db.models.pipeline import PipelineRun

    username = getattr(user, 'username', str(user))

    run = PipelineRun.query.get(run_id)
    if not run:
        raise NotFoundError(f'Pipeline run {run_id} not found')

    if run.created_by == username:
        return

    raise ForbiddenError('You do not have access to this pipeline run')


def require_oncoco_analysis_owner(analysis_id: int, user) -> None:
    """
    Prüft ob der User Eigentümer der OnCoCo-Analyse ist.

    Zugriff haben:
    - Admins (Bypass)
    - Analyse-Ersteller (user_id == username)

    Args:
        analysis_id: OnCoCoAnalysis-ID
        user: User-Objekt aus g.authentik_user

    Raises:
        ForbiddenError: User ist nicht der Eigentümer
        NotFoundError: Analyse existiert nicht
    """
    from decorators.permission_decorator import has_role
    if has_role(user, 'admin'):
        return

    from db.tables import OnCoCoAnalysis

    username = getattr(user, 'username', str(user))

    analysis = OnCoCoAnalysis.query.get(analysis_id)
    if not analysis:
        raise NotFoundError(f'Analysis {analysis_id} not found')

    if analysis.user_id == username:
        return

    raise ForbiddenError('You do not have access to this analysis')
