"""
Wizard Service for programmatic Scenario Wizard access.

Enables Claude Code and other API clients to use the full Scenario Wizard
workflow without browser interaction.

Session Lifecycle:
1. create_session() → initialized
2. upload_files() → uploaded
3. analyze() → analyzed
4. configure() → configured
5. create_scenario() → created
"""

from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import uuid
import base64
import csv
import json
import io
import os

from services.data_import.schema_detector import SchemaDetector

logger = logging.getLogger(__name__)


class WizardStatus(Enum):
    """Wizard session status."""
    INITIALIZED = "initialized"
    UPLOADED = "uploaded"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    CONFIGURED = "configured"
    CREATING = "creating"
    CREATED = "created"
    ERROR = "error"


@dataclass
class WizardFile:
    """Uploaded file metadata."""
    filename: str
    size: int
    rows: int = 0
    columns: list[str] = field(default_factory=list)
    content_type: str = "text/csv"


@dataclass
class WizardConfig:
    """Scenario configuration."""
    scenario_name: str = ""
    eval_type: str = ""
    preset: Optional[str] = None

    # Type-specific config
    dimensions: Optional[list[dict]] = None
    labels: Optional[list[dict]] = None
    buckets: Optional[list[dict]] = None
    scale: Optional[dict] = None

    # Users
    owner_id: Optional[int] = None
    evaluator_ids: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "scenario_name": self.scenario_name,
            "eval_type": self.eval_type,
            "preset": self.preset,
            "dimensions": self.dimensions,
            "labels": self.labels,
            "buckets": self.buckets,
            "scale": self.scale,
            "owner_id": self.owner_id,
            "evaluator_ids": self.evaluator_ids,
        }


@dataclass
class WizardSession:
    """Wizard session state."""
    session_id: str
    created_at: datetime
    expires_at: datetime
    status: WizardStatus = WizardStatus.INITIALIZED

    # Step 1: Files
    files: list[WizardFile] = field(default_factory=list)
    raw_data: list[dict] = field(default_factory=list)

    # Step 2: Analysis
    analysis: dict = field(default_factory=dict)
    detected_type: Optional[str] = None
    field_mapping: dict = field(default_factory=dict)

    # Step 3: Configuration
    config: WizardConfig = field(default_factory=WizardConfig)

    # Step 4: Result
    scenario_id: Optional[int] = None
    scenario_url: Optional[str] = None

    # Errors and warnings
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status.value,
            "files": [
                {
                    "filename": f.filename,
                    "size": f.size,
                    "rows": f.rows,
                    "columns": f.columns,
                }
                for f in self.files
            ],
            "analysis": self.analysis,
            "detected_type": self.detected_type,
            "field_mapping": self.field_mapping,
            "config": self.config.to_dict(),
            "scenario_id": self.scenario_id,
            "scenario_url": self.scenario_url,
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def get_next_step(self) -> str:
        """Get the next recommended step."""
        step_map = {
            WizardStatus.INITIALIZED: "upload",
            WizardStatus.UPLOADED: "analyze",
            WizardStatus.ANALYZING: "wait",
            WizardStatus.ANALYZED: "configure",
            WizardStatus.CONFIGURED: "create",
            WizardStatus.CREATING: "wait",
            WizardStatus.CREATED: "done",
            WizardStatus.ERROR: "fix_errors",
        }
        return step_map.get(self.status, "unknown")

    def get_available_actions(self) -> list[str]:
        """Get available actions for current state."""
        action_map = {
            WizardStatus.INITIALIZED: ["upload", "delete"],
            WizardStatus.UPLOADED: ["analyze", "upload", "delete"],
            WizardStatus.ANALYZING: ["delete"],
            WizardStatus.ANALYZED: ["configure", "analyze", "delete"],
            WizardStatus.CONFIGURED: ["create", "configure", "preview", "delete"],
            WizardStatus.CREATING: [],
            WizardStatus.CREATED: ["delete"],
            WizardStatus.ERROR: ["delete", "retry"],
        }
        return action_map.get(self.status, [])


class WizardService:
    """
    Service for managing Wizard sessions.

    Handles the full lifecycle of programmatic scenario creation.
    """

    # Session storage (in production, use Redis)
    _sessions: dict[str, WizardSession] = {}

    # Session TTL
    SESSION_TTL_HOURS = 1

    def __init__(self):
        """Initialize the wizard service."""
        self._ai_analyzer = None

    def _get_ai_analyzer(self):
        """Lazy load AI analyzer to avoid import issues."""
        if self._ai_analyzer is None:
            from services.data_import.ai_analyzer import AIAnalyzer
            self._ai_analyzer = AIAnalyzer()
        return self._ai_analyzer

    def create_session(self) -> WizardSession:
        """
        Create a new wizard session.

        Returns:
            New WizardSession with unique ID
        """
        now = datetime.now()
        session = WizardSession(
            session_id=f"wiz_{uuid.uuid4().hex[:12]}",
            created_at=now,
            expires_at=now + timedelta(hours=self.SESSION_TTL_HOURS),
        )
        self._sessions[session.session_id] = session
        logger.info(f"Wizard session created: {session.session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[WizardSession]:
        """
        Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            WizardSession or None if not found/expired
        """
        session = self._sessions.get(session_id)
        if session and session.expires_at < datetime.now():
            # Session expired
            self.delete_session(session_id)
            return None
        return session

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Wizard session deleted: {session_id}")
            return True
        return False

    def upload_file_base64(
        self,
        session_id: str,
        filename: str,
        content_base64: str
    ) -> WizardSession:
        """
        Upload a file via base64 encoding.

        Args:
            session_id: Session ID
            filename: Original filename
            content_base64: Base64-encoded file content

        Returns:
            Updated WizardSession
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        try:
            # Decode base64
            content = base64.b64decode(content_base64)
            return self._process_file(session, filename, content)
        except Exception as e:
            session.status = WizardStatus.ERROR
            session.errors.append(f"Base64 decode failed: {str(e)}")
            raise

    def upload_file_local(
        self,
        session_id: str,
        file_path: str
    ) -> WizardSession:
        """
        Upload a file from local filesystem (Development only!).

        Args:
            session_id: Session ID
            file_path: Absolute path to file

        Returns:
            Updated WizardSession
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if not os.path.exists(file_path):
            session.status = WizardStatus.ERROR
            session.errors.append(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            filename = os.path.basename(file_path)
            return self._process_file(session, filename, content)
        except Exception as e:
            session.status = WizardStatus.ERROR
            session.errors.append(f"File read failed: {str(e)}")
            raise

    def _process_file(
        self,
        session: WizardSession,
        filename: str,
        content: bytes
    ) -> WizardSession:
        """
        Process uploaded file content.

        Args:
            session: Wizard session
            filename: Filename
            content: Raw file content

        Returns:
            Updated session
        """
        try:
            # Detect file type and parse
            if filename.endswith('.csv'):
                data, columns, rows = self._parse_csv(content)
            elif filename.endswith('.json'):
                data, columns, rows = self._parse_json(content)
            elif filename.endswith('.jsonl'):
                data, columns, rows = self._parse_jsonl(content)
            else:
                raise ValueError(f"Unsupported file type: {filename}")

            # Store file info
            wizard_file = WizardFile(
                filename=filename,
                size=len(content),
                rows=rows,
                columns=columns,
            )
            session.files.append(wizard_file)
            session.raw_data = data
            session.status = WizardStatus.UPLOADED

            logger.info(f"Wizard file uploaded: {filename} ({rows} rows, {len(columns)} columns)")
            return session

        except Exception as e:
            session.status = WizardStatus.ERROR
            session.errors.append(f"File parse failed: {str(e)}")
            raise

    def _parse_csv(self, content: bytes) -> tuple[list[dict], list[str], int]:
        """Parse CSV content."""
        text = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(text))
        data = list(reader)
        columns = list(data[0].keys()) if data else []
        return data, columns, len(data)

    def _parse_json(self, content: bytes) -> tuple[list[dict], list[str], int]:
        """Parse JSON content."""
        text = content.decode('utf-8')
        parsed = json.loads(text)

        if isinstance(parsed, list):
            data = parsed
        elif isinstance(parsed, dict) and 'items' in parsed:
            data = parsed['items']
        elif isinstance(parsed, dict) and 'data' in parsed:
            data = parsed['data']
        else:
            data = [parsed]

        columns = list(data[0].keys()) if data and isinstance(data[0], dict) else []
        return data, columns, len(data)

    def _parse_jsonl(self, content: bytes) -> tuple[list[dict], list[str], int]:
        """Parse JSONL content."""
        text = content.decode('utf-8')
        data = []
        for line in text.strip().split('\n'):
            if line.strip():
                data.append(json.loads(line))

        columns = list(data[0].keys()) if data and isinstance(data[0], dict) else []
        return data, columns, len(data)

    def analyze(
        self,
        session_id: str,
        user_intent: Optional[str] = None
    ) -> WizardSession:
        """
        Run AI analysis on uploaded data.

        Args:
            session_id: Session ID
            user_intent: Optional user description of what they want

        Returns:
            Updated WizardSession with analysis results
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if not session.raw_data:
            session.status = WizardStatus.ERROR
            session.errors.append("No data to analyze. Upload a file first.")
            raise ValueError("No data to analyze")

        session.status = WizardStatus.ANALYZING

        try:
            ai_analyzer = self._get_ai_analyzer()
            filename = session.files[0].filename if session.files else None

            # STEP 1: Schema detection FIRST (authenticity, comparison, etc.)
            schema_detector = SchemaDetector()
            schema_result = schema_detector.detect(session.raw_data, filename)

            if schema_result.confidence == 'definite' and schema_result.eval_type:
                logger.info(f"Schema detected {schema_result.eval_type.value} for {filename}")
                # Use AI analyzer with fixed type for config generation
                result = ai_analyzer._generate_config_for_detected_type(
                    data=session.raw_data,
                    sample_json=json.dumps(
                        session.raw_data[:3] if isinstance(session.raw_data, list) else session.raw_data,
                        indent=2,
                        ensure_ascii=False,
                        default=str
                    )[:3500],
                    schema_result=schema_result,
                    user_intent=user_intent,
                    filename=filename
                )
                session.analysis = result
                session.detected_type = result.get('task_type')
                session.field_mapping = result.get('field_mapping', {})
                session.config.eval_type = session.detected_type or ""
                session.config.scenario_name = self._generate_scenario_name(filename)
                session.config.preset = result.get('recommended_preset')
                session.status = WizardStatus.ANALYZED
                logger.info(f"Schema-based analysis complete: {session.detected_type}")
                return session

            # STEP 2: Check for Long-Format (only if schema detection was uncertain)
            is_long_format = ai_analyzer._detect_long_format(session.raw_data)

            if is_long_format:
                logger.info(f"Long-Format detected for {filename}")

                # Generate field mapping for Long-Format
                field_mapping = ai_analyzer.generate_field_mapping(
                    data=session.raw_data,
                    detected_type='ranking',  # Long-Format = Ranking
                    detected_format='long',
                    filename=filename
                )

                if field_mapping.get('success') and field_mapping.get('format') == 'long':
                    session.field_mapping = field_mapping
                    session.detected_type = 'ranking'

                    # Build analysis result
                    session.analysis = {
                        "eval_type": "ranking",
                        "confidence": 0.95,
                        "detected_format": "long",
                        "field_mapping": field_mapping,
                        "unique_groups": field_mapping.get('unique_groups', 0),
                        "variants_per_group": field_mapping.get('variants_per_group', 0),
                        "reasoning": f"Long-Format detected: {field_mapping.get('variants_per_group', 0)} variants per group = Ranking",
                        "recommended_preset": "buckets-3",
                    }

                    # Suggest default config
                    session.config.eval_type = "ranking"
                    session.config.scenario_name = self._generate_scenario_name(filename)
                    session.config.preset = "buckets-3"
                    session.config.buckets = [
                        {"name": "Best", "order": 1, "color": "#98d4bb"},
                        {"name": "Good", "order": 2, "color": "#D1BC8A"},
                        {"name": "Poor", "order": 3, "color": "#e8a087"},
                    ]

                    session.status = WizardStatus.ANALYZED
                    logger.info(f"Long-Format analysis complete: {session.detected_type}")
                    return session

            # STEP 3: Standard analysis via AI
            if user_intent:
                result = ai_analyzer.analyze_intent(
                    data=session.raw_data,
                    user_intent=user_intent,
                    filename=filename,
                    file_count=len(session.files),
                )
            else:
                result = ai_analyzer.analyze_structure(
                    data=session.raw_data,
                    filename=filename,
                )

            session.analysis = result
            session.detected_type = result.get('suggested_task_type') or result.get('task_type')
            session.field_mapping = result.get('field_mapping', {})

            # Set default config from analysis
            session.config.eval_type = session.detected_type or ""
            session.config.scenario_name = self._generate_scenario_name(filename)
            session.config.preset = result.get('recommended_preset')

            session.status = WizardStatus.ANALYZED
            logger.info(f"Analysis complete: {session.detected_type}")
            return session

        except Exception as e:
            session.status = WizardStatus.ERROR
            session.errors.append(f"Analysis failed: {str(e)}")
            logger.exception(f"Wizard analysis failed: {e}")
            raise

    def _generate_scenario_name(self, filename: Optional[str]) -> str:
        """Generate a default scenario name from filename."""
        if not filename:
            return f"Scenario {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # Remove extension and clean up
        name = os.path.splitext(filename)[0]
        name = name.replace('_', ' ').replace('-', ' ')
        name = ' '.join(word.capitalize() for word in name.split())
        return name

    def configure(
        self,
        session_id: str,
        config: dict
    ) -> WizardSession:
        """
        Update session configuration.

        Args:
            session_id: Session ID
            config: Configuration dict

        Returns:
            Updated WizardSession
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Update config fields
        if 'scenario_name' in config:
            session.config.scenario_name = config['scenario_name']
        if 'eval_type' in config:
            session.config.eval_type = config['eval_type']
        if 'preset' in config:
            session.config.preset = config['preset']
        if 'dimensions' in config:
            session.config.dimensions = config['dimensions']
        if 'labels' in config:
            session.config.labels = config['labels']
        if 'buckets' in config:
            session.config.buckets = config['buckets']
        if 'scale' in config:
            session.config.scale = config['scale']
        if 'owner_id' in config:
            session.config.owner_id = config['owner_id']
        if 'evaluator_ids' in config:
            session.config.evaluator_ids = config['evaluator_ids']

        session.status = WizardStatus.CONFIGURED
        logger.info(f"Wizard config updated: {session.config.scenario_name}")
        return session

    def get_preview(
        self,
        session_id: str,
        count: int = 5
    ) -> dict:
        """
        Get preview of transformed items.

        Args:
            session_id: Session ID
            count: Number of items to preview

        Returns:
            Preview data
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if not session.raw_data:
            return {"items": [], "total_count": 0}

        ai_analyzer = self._get_ai_analyzer()

        # Transform if Long-Format
        if session.field_mapping.get('format') == 'long':
            transformed = ai_analyzer.transform_long_format_to_ranking(
                session.raw_data,
                session.field_mapping
            )
        else:
            transformed = session.raw_data

        return {
            "items": transformed[:count],
            "total_count": len(transformed),
            "eval_type": session.config.eval_type,
        }

    def create_scenario(self, session_id: str) -> WizardSession:
        """
        Create the scenario from session data.

        Args:
            session_id: Session ID

        Returns:
            Updated WizardSession with scenario_id
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if not session.config.scenario_name:
            session.errors.append("Scenario name is required")
            raise ValueError("Scenario name is required")

        if not session.config.eval_type:
            session.errors.append("Evaluation type is required")
            raise ValueError("Evaluation type is required")

        session.status = WizardStatus.CREATING

        try:
            from services.data_import import ImportService
            from services.data_import.adapters.base_adapter import TaskType

            ai_analyzer = self._get_ai_analyzer()
            import_service = ImportService()

            # Transform data if Long-Format
            items = session.raw_data
            if session.field_mapping.get('format') == 'long':
                items = ai_analyzer.transform_long_format_to_ranking(
                    session.raw_data,
                    session.field_mapping
                )

            # Map eval_type to TaskType
            task_type_map = {
                'ranking': TaskType.RANKING,
                'rating': TaskType.RATING,
                'comparison': TaskType.COMPARISON,
                'authenticity': TaskType.AUTHENTICITY,
                'labeling': TaskType.LABELING,
                'mail_rating': TaskType.MAIL_RATING,
            }
            task_type = task_type_map.get(session.config.eval_type, TaskType.RATING)

            # Create import session
            import_session = import_service.create_session_from_data(
                data=items,
                task_type=task_type,
                filename=session.config.scenario_name
            )

            # Build AI analysis for transformation
            ai_analysis = {
                'task_type': session.config.eval_type,
                'field_mapping': session.field_mapping,
                'role_mapping': {'user': 'Klient', 'assistant': 'Berater'},
            }

            # Transform
            import_session = import_service.transform_with_ai(
                import_session.session_id,
                ai_analysis=ai_analysis
            )

            if import_session.status == "error":
                raise ValueError(f"Transform failed: {import_session.errors}")

            # Build scenario config
            scenario_config = {
                'status': 'evaluating',  # Default status for new scenarios
            }
            if session.config.dimensions:
                scenario_config['dimensions'] = session.config.dimensions
            if session.config.labels:
                scenario_config['labels'] = session.config.labels
            if session.config.buckets:
                scenario_config['buckets'] = session.config.buckets
            if session.config.scale:
                scenario_config['scale'] = session.config.scale
            if session.config.preset:
                scenario_config['preset'] = session.config.preset

            # Execute import and create scenario
            import_session = import_service.execute_import(
                session_id=import_session.session_id,
                task_type=task_type,
                source_name=session.config.scenario_name,
                create_scenario=True,
                ai_analysis={'config': scenario_config} if scenario_config else None
            )

            if import_session.status == "error":
                raise ValueError(f"Import failed: {import_session.errors}")

            # Update wizard session
            session.scenario_id = import_session.options.get('scenario_id')
            session.scenario_url = f"/scenarios/{session.scenario_id}/evaluate"
            session.status = WizardStatus.CREATED
            session.warnings.extend(import_session.warnings)

            logger.info(f"Wizard scenario created: {session.scenario_id}")

            # Assign users to scenario
            self._assign_scenario_users(
                session.scenario_id,
                session.config.owner_id,
                session.config.evaluator_ids
            )

            # Cleanup import session
            import_service.delete_session(import_session.session_id)

            return session

        except Exception as e:
            session.status = WizardStatus.ERROR
            session.errors.append(f"Scenario creation failed: {str(e)}")
            logger.exception(f"Wizard create_scenario failed: {e}")
            raise

    def _assign_scenario_users(
        self,
        scenario_id: int,
        owner_id: Optional[int],
        evaluator_ids: list[int]
    ) -> None:
        """
        Assign users to the created scenario.

        Args:
            scenario_id: The created scenario ID
            owner_id: User ID of the owner (optional, defaults to admin)
            evaluator_ids: List of evaluator user IDs
        """
        from db import db
        from db.tables import ScenarioUsers, User, ScenarioRoles
        from db.models.scenario import InvitationStatus, MembershipStatus

        # Get admin user as fallback owner
        admin = User.query.filter_by(username='admin').first()

        # Determine owner
        actual_owner_id = owner_id
        if not actual_owner_id and admin:
            actual_owner_id = admin.id

        # Get owner username for invited_by field
        owner_user = User.query.get(actual_owner_id) if actual_owner_id else admin
        owner_username = owner_user.username if owner_user else 'system'

        assigned_user_ids = set()

        # Add owner as VIEWER (ownership is determined by created_by field)
        if actual_owner_id:
            owner_assignment = ScenarioUsers(
                scenario_id=scenario_id,
                user_id=actual_owner_id,
                role=ScenarioRoles.VIEWER,
                invitation_status=InvitationStatus.ACCEPTED,
                membership_status=MembershipStatus.ACTIVE,
                invited_at=datetime.utcnow(),
                invited_by=owner_username
            )
            db.session.add(owner_assignment)
            assigned_user_ids.add(actual_owner_id)
            logger.info(f"Assigned owner as viewer (user_id={actual_owner_id}) to scenario {scenario_id}")

        # Add evaluators
        for evaluator_id in evaluator_ids:
            if evaluator_id not in assigned_user_ids:
                evaluator_assignment = ScenarioUsers(
                    scenario_id=scenario_id,
                    user_id=evaluator_id,
                    role=ScenarioRoles.EVALUATOR,
                    invitation_status=InvitationStatus.ACCEPTED,
                    membership_status=MembershipStatus.ACTIVE,
                    invited_at=datetime.utcnow(),
                    invited_by=owner_username
                )
                db.session.add(evaluator_assignment)
                assigned_user_ids.add(evaluator_id)
                logger.info(f"Assigned evaluator (user_id={evaluator_id}) to scenario {scenario_id}")

        # Add admin as viewer if not already assigned
        if admin and admin.id not in assigned_user_ids:
            viewer_assignment = ScenarioUsers(
                scenario_id=scenario_id,
                user_id=admin.id,
                role=ScenarioRoles.VIEWER,
                invitation_status=InvitationStatus.ACCEPTED,
                membership_status=MembershipStatus.ACTIVE,
                invited_at=datetime.utcnow(),
                invited_by=owner_username
            )
            db.session.add(viewer_assignment)
            logger.info(f"Assigned admin as viewer to scenario {scenario_id}")

        db.session.commit()

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now()
        expired = [
            sid for sid, session in self._sessions.items()
            if session.expires_at < now
        ]
        for sid in expired:
            del self._sessions[sid]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired wizard sessions")

        return len(expired)


# Singleton instance
_wizard_service: Optional[WizardService] = None


def get_wizard_service() -> WizardService:
    """Get or create the singleton WizardService instance."""
    global _wizard_service
    if _wizard_service is None:
        _wizard_service = WizardService()
    return _wizard_service
