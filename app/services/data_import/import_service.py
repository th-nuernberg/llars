"""
Main Import Service for LLARS data import.

Orchestrates the entire import process: detection, transformation,
validation, and database insertion.
"""

from typing import Any
from dataclasses import dataclass, field
from datetime import datetime
import logging
import uuid
import hashlib

from db.database import db
from db.models.scenario import EmailThread, Message as DBMessage, RatingScenarios, ScenarioThreads

from .format_detector import FormatDetector
from .schema_validator import SchemaValidator, ValidationResult
from .adapters.base_adapter import AdapterResult, ImportItem, TaskType, ItemType, MessageRole
from .universal_transformer import UniversalTransformer, TransformConfig

logger = logging.getLogger(__name__)


@dataclass
class ImportSession:
    """Represents an import session with all its state."""
    session_id: str
    created_at: datetime
    status: str = "pending"  # pending, analyzing, transforming, validating, importing, complete, error
    filename: str | None = None
    file_size: int = 0

    # Detection results
    detected_format: str | None = None
    format_confidence: float = 0.0
    structure: dict[str, Any] = field(default_factory=dict)

    # Raw and transformed data
    raw_data: Any = None
    transformed_items: list[ImportItem] = field(default_factory=list)

    # Validation results
    validation_result: ValidationResult | None = None

    # Import configuration
    task_type: TaskType | None = None
    options: dict[str, Any] = field(default_factory=dict)

    # Results
    imported_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        result = {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "filename": self.filename,
            "file_size": self.file_size,
            "detected_format": self.detected_format,
            "format_confidence": self.format_confidence,
            "structure": self.structure,
            "item_count": len(self.transformed_items),
            "task_type": self.task_type.value if self.task_type else None,
            "validation": {
                "valid": self.validation_result.valid if self.validation_result else None,
                "errors": self.validation_result.errors if self.validation_result else [],
                "warnings": self.validation_result.warnings if self.validation_result else [],
                "stats": self.validation_result.stats if self.validation_result else {},
            },
            "imported_count": self.imported_count,
            "errors": self.errors,
            "warnings": self.warnings,
        }
        # Add scenario info if created
        if self.options.get("scenario_id"):
            result["scenario"] = {
                "id": self.options["scenario_id"],
                "name": self.options.get("scenario_name"),
            }
        return result


class ImportService:
    """
    Main service for data import operations.

    Handles the full lifecycle: upload, detection, transformation,
    validation, and database insertion.
    """

    # Active sessions (in production, use Redis)
    _sessions: dict[str, ImportSession] = {}

    def __init__(self):
        """Initialize the import service."""
        self.detector = FormatDetector()
        self.validator = SchemaValidator()
        self.universal_transformer = UniversalTransformer()

    def create_session(self, filename: str | None = None, file_size: int = 0) -> ImportSession:
        """Create a new import session."""
        session = ImportSession(
            session_id=str(uuid.uuid4()),
            created_at=datetime.now(),
            filename=filename,
            file_size=file_size,
        )
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> ImportSession | None:
        """Get an existing session."""
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def analyze_file(
        self,
        session_id: str,
        content: str | bytes,
        filename: str
    ) -> ImportSession:
        """
        Analyze uploaded file and detect format.

        Args:
            session_id: Session ID
            content: File content
            filename: Original filename

        Returns:
            Updated session with detection results
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session.status = "analyzing"
        session.filename = filename

        try:
            # Detect format
            result = self.detector.detect_from_file(content, filename)

            if not result["detected"]:
                session.status = "error"
                session.errors.append(result.get("parse_error", "Unknown format"))
                return session

            session.detected_format = result["format_id"]
            session.format_confidence = result["confidence"]
            session.structure = result.get("structure", {})
            session.raw_data = result.get("data")

            # Suggest task type from structure
            if "suggested_task_type" in result:
                session.task_type = TaskType(result["suggested_task_type"])

            session.status = "analyzed"

        except Exception as e:
            logger.exception(f"Error analyzing file: {e}")
            session.status = "error"
            session.errors.append(str(e))

        return session

    def transform(
        self,
        session_id: str,
        options: dict[str, Any] | None = None
    ) -> ImportSession:
        """
        Transform raw data to LLARS format.

        Args:
            session_id: Session ID
            options: Transformation options (field mappings, etc.)

        Returns:
            Updated session with transformed items
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if not session.raw_data:
            session.errors.append("No data to transform")
            return session

        session.status = "transforming"
        session.options = options or {}

        try:
            # Get adapter
            adapter = self.detector.get_adapter(session.detected_format)
            if not adapter:
                session.status = "error"
                session.errors.append(f"No adapter for format: {session.detected_format}")
                return session

            # Transform
            result: AdapterResult = adapter.transform(session.raw_data, options)

            session.transformed_items = result.items
            session.errors.extend(result.errors)
            session.warnings.extend(result.warnings)

            if result.suggested_task_type:
                session.task_type = result.suggested_task_type

            if result.success:
                session.status = "transformed"
            else:
                session.status = "error"

        except Exception as e:
            logger.exception(f"Error transforming data: {e}")
            session.status = "error"
            session.errors.append(str(e))

        return session

    def transform_with_ai(
        self,
        session_id: str,
        ai_analysis: dict[str, Any]
    ) -> ImportSession:
        """
        Transform raw data using AI-generated field mappings.

        This is the main method for the "conversational import" workflow.
        It uses the UniversalTransformer to apply AI-analyzed mappings
        to arbitrary data structures.

        Args:
            session_id: Session ID
            ai_analysis: Result from AIAnalyzer.analyze_intent()

        Returns:
            Updated session with transformed items
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if not session.raw_data:
            session.errors.append("No data to transform")
            return session

        session.status = "transforming"

        try:
            # Use universal transformer with AI analysis
            result: AdapterResult = self.universal_transformer.transform(
                session.raw_data,
                ai_analysis=ai_analysis
            )

            session.transformed_items = result.items
            session.errors.extend(result.errors)
            session.warnings.extend(result.warnings)

            if result.suggested_task_type:
                session.task_type = result.suggested_task_type

            if result.success:
                session.status = "transformed"
                logger.info(
                    f"AI transform complete: {len(result.items)} items, "
                    f"task_type={result.suggested_task_type}"
                )
            else:
                session.status = "error"

        except Exception as e:
            logger.exception(f"Error in AI transform: {e}")
            session.status = "error"
            session.errors.append(str(e))

        return session

    def validate(self, session_id: str) -> ImportSession:
        """
        Validate transformed data.

        Args:
            session_id: Session ID

        Returns:
            Updated session with validation results
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if not session.transformed_items:
            session.errors.append("No items to validate")
            return session

        session.status = "validating"

        try:
            # Convert ImportItems to dicts for validation
            items_dicts = [item.to_dict() for item in session.transformed_items]
            result = self.validator.validate_items_list(items_dicts)

            session.validation_result = result
            session.errors.extend(result.errors)
            session.warnings.extend(result.warnings)

            if result.valid:
                session.status = "validated"
            else:
                session.status = "validation_failed"

        except Exception as e:
            logger.exception(f"Error validating data: {e}")
            session.status = "error"
            session.errors.append(str(e))

        return session

    def execute_import(
        self,
        session_id: str,
        task_type: TaskType | None = None,
        source_name: str | None = None,
        create_scenario: bool = True,
        created_by: str | None = None,
        ai_analysis: dict | None = None
    ) -> ImportSession:
        """
        Execute the import and create database records.

        Args:
            session_id: Session ID
            task_type: Override task type
            source_name: Name for the import source
            create_scenario: Whether to create a scenario for the imported data
            created_by: Username of creator (for scenario)
            ai_analysis: AI analysis result with evaluation criteria etc.

        Returns:
            Updated session with import results
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if not session.transformed_items:
            session.errors.append("No items to import")
            return session

        session.status = "importing"

        # Use provided task type or session default
        final_task_type = task_type or session.task_type or TaskType.MAIL_RATING
        source = source_name or f"Import-{session.session_id[:8]}"

        try:
            imported = 0
            imported_threads = []

            for item in session.transformed_items:
                try:
                    thread = self._create_thread(item, final_task_type, source)
                    if thread:
                        imported += 1
                        imported_threads.append(thread)
                except Exception as e:
                    session.warnings.append(f"Failed to import item {item.id}: {str(e)}")

            db.session.flush()

            # Create scenario and link threads
            scenario = None
            if create_scenario and imported_threads:
                scenario = self._create_scenario(
                    source_name=source,
                    task_type=final_task_type,
                    threads=imported_threads,
                    created_by=created_by,
                    ai_analysis=ai_analysis
                )

            db.session.commit()

            session.imported_count = imported
            session.status = "complete"

            # Add scenario info to session options for API response
            if scenario:
                session.options["scenario_id"] = scenario.id
                session.options["scenario_name"] = scenario.scenario_name

            logger.info(
                f"Import complete: {imported}/{len(session.transformed_items)} items imported"
                + (f", scenario_id={scenario.id}" if scenario else "")
            )

        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error executing import: {e}")
            session.status = "error"
            session.errors.append(str(e))

        return session

    def _create_thread(
        self,
        item: ImportItem,
        task_type: TaskType,
        source: str
    ) -> EmailThread | None:
        """Create a database thread from an ImportItem."""
        # Map task type to function_type_id
        task_type_mapping = {
            TaskType.RANKING: 1,
            TaskType.RATING: 2,
            TaskType.MAIL_RATING: 3,
            TaskType.COMPARISON: 4,
            TaskType.AUTHENTICITY: 5,
            TaskType.JUDGE: 6,
            TaskType.TEXT_CLASSIFICATION: 7,
            TaskType.TEXT_RATING: 8,
        }
        function_type_id = task_type_mapping.get(task_type, 3)

        # Generate unique chat_id (must fit in signed INT: max 2,147,483,647)
        hash_value = int(hashlib.md5(item.id.encode()).hexdigest()[:8], 16)
        chat_id = hash_value % 2147483647  # Ensure within signed INT range

        # Check for existing thread
        existing = EmailThread.query.filter_by(
            chat_id=chat_id,
            function_type_id=function_type_id
        ).first()

        if existing:
            logger.debug(f"Thread already exists: {item.id}")
            return existing

        # Determine subject based on item type
        subject = item.subject or item.title or f"Imported: {item.id}"

        # Create thread
        thread = EmailThread(
            chat_id=chat_id,
            subject=subject,
            sender=source,
            function_type_id=function_type_id,
        )
        db.session.add(thread)
        db.session.flush()  # Get thread_id

        # Create messages based on ItemType
        self._create_messages_for_item(thread, item, source)

        return thread

    def _create_messages_for_item(
        self,
        thread: EmailThread,
        item: ImportItem,
        source: str
    ) -> None:
        """Create database messages based on the item type."""
        now = datetime.now()

        if item.item_type == ItemType.CONVERSATION:
            # Multi-turn conversation
            for msg in item.conversation:
                sender = self._map_role_to_sender(msg.role)
                db_message = DBMessage(
                    thread_id=thread.thread_id,
                    sender=sender,
                    content=msg.content,
                    timestamp=datetime.fromisoformat(msg.timestamp) if msg.timestamp else now,
                    generated_by=source,
                )
                db.session.add(db_message)

        elif item.item_type == ItemType.SINGLE_TEXT:
            # Single text item (review, document, etc.)
            db_message = DBMessage(
                thread_id=thread.thread_id,
                sender="Content",
                content=item.content or "",
                timestamp=now,
                generated_by=source,
            )
            db.session.add(db_message)

            # Store metadata as system message if present
            if item.label or item.category:
                meta_content = []
                if item.label:
                    meta_content.append(f"Label: {item.label}")
                if item.category:
                    meta_content.append(f"Category: {item.category}")

                db_meta = DBMessage(
                    thread_id=thread.thread_id,
                    sender="System",
                    content=" | ".join(meta_content),
                    timestamp=now,
                    generated_by=source,
                )
                db.session.add(db_meta)

        elif item.item_type == ItemType.QA_PAIR:
            # Question-Answer pair
            if item.question:
                db_question = DBMessage(
                    thread_id=thread.thread_id,
                    sender="Klient",  # Question = User
                    content=item.question,
                    timestamp=now,
                    generated_by=source,
                )
                db.session.add(db_question)

            if item.answer:
                db_answer = DBMessage(
                    thread_id=thread.thread_id,
                    sender="Berater",  # Answer = Assistant
                    content=item.answer,
                    timestamp=now,
                    generated_by=source,
                )
                db.session.add(db_answer)

        elif item.item_type == ItemType.TEXT_PAIR:
            # Two texts for comparison (A/B testing, chosen/rejected, etc.)
            label_a = item.label_a or "Text A"
            label_b = item.label_b or "Text B"

            if item.text_a:
                db_text_a = DBMessage(
                    thread_id=thread.thread_id,
                    sender=label_a,
                    content=item.text_a,
                    timestamp=now,
                    generated_by=source,
                )
                db.session.add(db_text_a)

            if item.text_b:
                db_text_b = DBMessage(
                    thread_id=thread.thread_id,
                    sender=label_b,
                    content=item.text_b,
                    timestamp=now,
                    generated_by=source,
                )
                db.session.add(db_text_b)

        elif item.item_type == ItemType.DOCUMENT:
            # Long-form document
            db_message = DBMessage(
                thread_id=thread.thread_id,
                sender="Document",
                content=item.content or "",
                timestamp=now,
                generated_by=source,
            )
            db.session.add(db_message)

        else:
            # CUSTOM or unknown - try to create from available content
            content = item.content or item.get_display_content()
            if content:
                db_message = DBMessage(
                    thread_id=thread.thread_id,
                    sender="Content",
                    content=content,
                    timestamp=now,
                    generated_by=source,
                )
                db.session.add(db_message)

    def _map_role_to_sender(self, role: MessageRole) -> str:
        """Map message role to sender string."""
        role_mapping = {
            MessageRole.USER: "Klient",
            MessageRole.ASSISTANT: "Berater",
            MessageRole.SYSTEM: "System",
        }
        return role_mapping.get(role, "Unknown")

    def get_sample(self, session_id: str, count: int = 5) -> list[dict[str, Any]]:
        """Get a sample of transformed items for preview."""
        session = self.get_session(session_id)
        if not session or not session.transformed_items:
            return []

        sample = session.transformed_items[:count]
        return [item.to_dict() for item in sample]

    def _create_scenario(
        self,
        source_name: str,
        task_type: TaskType,
        threads: list[EmailThread],
        created_by: str | None,
        ai_analysis: dict | None
    ) -> RatingScenarios:
        """
        Create a scenario for imported data and link threads.

        Args:
            source_name: Name for the scenario
            task_type: Task type for the scenario
            threads: List of imported EmailThread objects
            created_by: Username of creator
            ai_analysis: AI analysis result (may contain evaluation_criteria, classification_labels)

        Returns:
            Created RatingScenarios object
        """
        # Map task type to function_type_id
        task_type_mapping = {
            TaskType.RANKING: 1,
            TaskType.RATING: 2,
            TaskType.MAIL_RATING: 3,
            TaskType.COMPARISON: 4,
            TaskType.AUTHENTICITY: 5,
            TaskType.JUDGE: 6,
            TaskType.TEXT_CLASSIFICATION: 7,
            TaskType.TEXT_RATING: 8,
        }
        function_type_id = task_type_mapping.get(task_type, 3)

        # Build config_json from AI analysis
        config_json = {}
        if ai_analysis:
            # Include evaluation criteria if present
            if 'evaluation_criteria' in ai_analysis:
                config_json['evaluation_criteria'] = ai_analysis['evaluation_criteria']

            # Include classification labels if present (for text_classification)
            if 'classification_labels' in ai_analysis:
                config_json['classification_labels'] = ai_analysis['classification_labels']

            # Include task description
            if 'task_description' in ai_analysis:
                config_json['task_description'] = ai_analysis['task_description']

            # Include any custom config
            if 'config' in ai_analysis:
                config_json.update(ai_analysis['config'])

        # Create scenario
        scenario = RatingScenarios(
            scenario_name=source_name,
            function_type_id=function_type_id,
            created_by=created_by,
            config_json=config_json if config_json else None,
        )
        db.session.add(scenario)
        db.session.flush()  # Get scenario ID

        # Link threads to scenario
        for thread in threads:
            scenario_thread = ScenarioThreads(
                scenario_id=scenario.id,
                thread_id=thread.thread_id,
            )
            db.session.add(scenario_thread)

        logger.info(
            f"Created scenario '{source_name}' (id={scenario.id}) "
            f"with {len(threads)} threads, task_type={task_type.value}"
        )

        return scenario

    def get_available_formats(self) -> list[dict[str, Any]]:
        """Get list of all supported formats."""
        return self.detector.available_formats
