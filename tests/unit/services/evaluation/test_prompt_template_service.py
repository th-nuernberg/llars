"""
Tests for PromptTemplateService.

Tests prompt template management, seeding defaults, and rendering.
"""

import pytest


class TestPromptTemplateService:
    """Tests for PromptTemplateService."""

    def test_PROMPT_001_seed_defaults_creates_templates(self, app, db):
        """Seeding defaults should create templates for all task types."""
        from services.evaluation.prompt_template_service import (
            PromptTemplateService,
            DEFAULT_PROMPTS,
        )
        from db.models import PromptTemplate

        with app.app_context():
            # Seed defaults
            created = PromptTemplateService.seed_defaults(created_by="test")

            # Verify all task types have templates
            assert len(created) == len(DEFAULT_PROMPTS)

            for task_type in DEFAULT_PROMPTS.keys():
                assert task_type in created
                template = PromptTemplate.query.get(created[task_type])
                assert template is not None
                assert template.task_type == task_type
                assert template.is_default is True
                assert template.is_active is True

    def test_PROMPT_002_seed_defaults_idempotent(self, app, db):
        """Seeding defaults multiple times should not create duplicates."""
        from services.evaluation.prompt_template_service import PromptTemplateService
        from db.models import PromptTemplate

        with app.app_context():
            # Seed twice
            first = PromptTemplateService.seed_defaults()
            second = PromptTemplateService.seed_defaults()

            # Should return same IDs
            assert first == second

            # Should only have one template per task type
            for task_type in first.keys():
                count = PromptTemplate.query.filter_by(
                    task_type=task_type,
                    is_default=True
                ).count()
                assert count == 1

    def test_PROMPT_003_get_template_for_task_returns_default(self, app, db):
        """Should return default template when no specific ID given."""
        from services.evaluation.prompt_template_service import PromptTemplateService

        with app.app_context():
            PromptTemplateService.seed_defaults()

            template = PromptTemplateService.get_template_for_task("ranking")
            assert template is not None
            assert template.task_type == "ranking"
            assert template.is_default is True

    def test_PROMPT_004_get_template_for_task_with_id(self, app, db):
        """Should return specific template when ID given."""
        from services.evaluation.prompt_template_service import PromptTemplateService

        with app.app_context():
            PromptTemplateService.seed_defaults()

            # Create a custom template
            custom = PromptTemplateService.create_template(
                name="Custom Rating Template",
                task_type="rating",
                system_prompt="Custom system prompt.",
                user_prompt_template="Custom user prompt with {features}.",
                variables=["features"],
            )

            # Should return custom when ID specified
            result = PromptTemplateService.get_template_for_task("rating", template_id=custom.id)
            assert result.id == custom.id
            assert result.name == "Custom Rating Template"

    def test_PROMPT_005_create_template(self, app, db):
        """Should create a new template."""
        from services.evaluation.prompt_template_service import PromptTemplateService
        from db.models import PromptTemplate

        with app.app_context():
            template = PromptTemplateService.create_template(
                name="Test Template",
                task_type="comparison",
                system_prompt="Test system prompt here.",
                user_prompt_template="Compare {text_a} with {text_b}.",
                variables=["text_a", "text_b"],
                is_default=False,
                created_by="tester",
            )

            assert template.id is not None
            assert template.name == "Test Template"
            assert template.task_type == "comparison"
            assert template.created_by == "tester"
            assert template.is_default is False

            # Verify in database
            found = PromptTemplate.query.get(template.id)
            assert found is not None

    def test_PROMPT_006_update_template_increments_version(self, app, db):
        """Updating prompt content should increment version."""
        from services.evaluation.prompt_template_service import PromptTemplateService

        with app.app_context():
            template = PromptTemplateService.create_template(
                name="Versioned Template",
                task_type="rating",
                system_prompt="Original prompt.",
                user_prompt_template="Original user prompt.",
            )

            original_version = template.version

            # Update the template
            updated = PromptTemplateService.update_template(
                template.id,
                system_prompt="Updated prompt content."
            )

            assert updated is not None
            assert updated.version != original_version

    def test_PROMPT_007_set_default(self, app, db):
        """Should set a template as default and unset previous default."""
        from services.evaluation.prompt_template_service import PromptTemplateService
        from db.models import PromptTemplate

        with app.app_context():
            PromptTemplateService.seed_defaults()

            # Create a new template
            new_template = PromptTemplateService.create_template(
                name="New Default",
                task_type="ranking",
                system_prompt="New default prompt.",
                user_prompt_template="New user prompt.",
            )

            assert new_template.is_default is False

            # Set as default
            success = PromptTemplateService.set_default(new_template.id)
            assert success is True

            # Refresh to get updated value
            db.session.refresh(new_template)
            assert new_template.is_default is True

            # Old default should no longer be default
            defaults = PromptTemplate.query.filter_by(
                task_type="ranking",
                is_default=True
            ).all()
            assert len(defaults) == 1
            assert defaults[0].id == new_template.id

    def test_PROMPT_008_render_prompt(self, app, db):
        """Should render prompt with variables."""
        from services.evaluation.prompt_template_service import PromptTemplateService
        from db.models import PromptTemplate

        with app.app_context():
            template = PromptTemplate(
                name="Test",
                task_type="rating",
                system_prompt="System",
                user_prompt_template="Rate these features: {features}\nContext: {thread_content}",
                variables=["features", "thread_content"],
            )

            rendered = PromptTemplateService.render_prompt(
                template,
                features="- Feature 1\n- Feature 2",
                thread_content="Client: Hello\nAdvisor: Hi"
            )

            assert "- Feature 1" in rendered
            assert "- Feature 2" in rendered
            assert "Client: Hello" in rendered
            assert "{features}" not in rendered

    def test_PROMPT_009_get_available_task_types(self, app, db):
        """Should return all available task types."""
        from services.evaluation.prompt_template_service import PromptTemplateService, DEFAULT_PROMPTS

        with app.app_context():
            task_types = PromptTemplateService.get_available_task_types()

            assert len(task_types) == len(DEFAULT_PROMPTS)
            assert "ranking" in task_types
            assert "rating" in task_types
            assert "authenticity" in task_types
            assert "mail_rating" in task_types
            assert "comparison" in task_types
            assert "text_classification" in task_types

    def test_PROMPT_010_get_all_for_task(self, app, db):
        """Should return all active templates for a task type."""
        from services.evaluation.prompt_template_service import PromptTemplateService

        with app.app_context():
            PromptTemplateService.seed_defaults()

            # Create additional templates
            PromptTemplateService.create_template(
                name="Custom 1",
                task_type="ranking",
                system_prompt="Custom 1",
                user_prompt_template="Custom 1",
            )
            PromptTemplateService.create_template(
                name="Custom 2",
                task_type="ranking",
                system_prompt="Custom 2",
                user_prompt_template="Custom 2",
            )

            templates = PromptTemplateService.get_all_for_task("ranking")

            assert len(templates) == 3  # 1 default + 2 custom
