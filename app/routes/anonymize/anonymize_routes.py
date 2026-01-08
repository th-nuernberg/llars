from __future__ import annotations

import io
import re
from typing import Any

from flask import jsonify, request
from pypdf import PdfReader
from docx.api import Document

from decorators.error_handler import handle_api_errors, ValidationError, ForbiddenError
from decorators.permission_decorator import require_permission
from routes.anonymize import anonymize_bp
from services.anonymize import AnonymizeService
from services.llm.llm_access_service import LLMAccessService
from auth.auth_utils import AuthUtils


def _extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    raw_text = "\n".join(p.text for p in doc.paragraphs)

    raw_text = raw_text.replace("\t\n", ". \n")
    raw_text = re.sub(r"\n{4,}", ". \n", raw_text)
    raw_text = re.sub(r"\n{3}", ". \n", raw_text)
    raw_text = re.sub(r"\n{2}", ". \n", raw_text)
    raw_text = raw_text.replace("\n", ". \n")
    raw_text = raw_text.replace(". . .", ".")
    raw_text = raw_text.replace(". .", ".")
    raw_text = raw_text.replace("..", ".")

    return raw_text.strip()


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    raw_text = ""
    for page in reader.pages:
        raw_text += page.extract_text() or ""

    raw_text = raw_text.replace("  ", " ")
    raw_text = raw_text.replace(" \n", " ")
    raw_text = raw_text.replace("\n", ".\n ")
    return raw_text.strip()


@anonymize_bp.route("/health", methods=["GET"])
@require_permission("feature:anonymize:view")
@handle_api_errors(logger_name="anonymize")
def anonymize_health() -> Any:
    mode = (request.args.get("mode") or "").strip().lower()
    full = (request.args.get("full") or "").strip().lower()
    if full in {"1", "true", "yes"}:
        mode = "full"

    # Default to a fast check to avoid loading large models (and nginx timeouts) on every page visit.
    # Use ?mode=full (or ?full=1) for a deep check that validates DB/NER/recommender by actually loading them.
    if mode == "full":
        status = AnonymizeService.health_check()
    else:
        status = AnonymizeService.quick_status()

    status["llm"] = AnonymizeService.llm_quick_status()
    status["mode"] = "full" if mode == "full" else "quick"
    return jsonify({"success": True, "status": status})


@anonymize_bp.route("/pseudonymize", methods=["POST"])
@require_permission("feature:anonymize:view")
@handle_api_errors(logger_name="anonymize")
def anonymize_pseudonymize() -> Any:
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "")
    if not isinstance(text, str):
        raise ValidationError("Field 'text' must be a string")

    engine = payload.get("engine") or "offline"
    if not isinstance(engine, str):
        raise ValidationError("Field 'engine' must be a string")
    engine = engine.strip().lower()
    if engine not in {"offline", "llm", "hybrid"}:
        raise ValidationError("Invalid engine. Allowed: offline, llm, hybrid")

    llm_model = payload.get("llm_model")
    if llm_model is not None and not isinstance(llm_model, str):
        raise ValidationError("Field 'llm_model' must be a string")
    if isinstance(llm_model, str) and llm_model.strip():
        from db.models.llm_model import LLMModel
        db_model = LLMModel.get_by_model_id(llm_model.strip())
        if not db_model or not db_model.is_active or db_model.model_type != LLMModel.MODEL_TYPE_LLM:
            raise ValidationError("Selected llm_model is not an active LLM model")
        username = AuthUtils.extract_username_without_validation()
        if not LLMAccessService.user_can_access_model(username, llm_model.strip()):
            raise ForbiddenError("Selected llm_model is not available for this user")

    status_offline = AnonymizeService.quick_status()
    status_llm = AnonymizeService.llm_quick_status()
    if engine in {"offline", "hybrid"} and not status_offline.get("ready"):
        return jsonify({
            "success": False,
            "error": "Anonymize resources/models are not ready",
            "code": "ANONYMIZE_NOT_READY",
            "status": status_offline,
        }), 503
    if engine in {"llm", "hybrid"} and not status_llm.get("ready"):
        return jsonify({
            "success": False,
            "error": "LLM for anonymization is not configured/ready",
            "code": "ANONYMIZE_LLM_NOT_READY",
            "status": status_llm,
        }), 503

    group_overrides = payload.get("group_overrides") or {}
    if not isinstance(group_overrides, dict):
        raise ValidationError("Field 'group_overrides' must be an object")

    date_shift_days = payload.get("date_shift_days")
    if date_shift_days is not None and not isinstance(date_shift_days, int):
        raise ValidationError("Field 'date_shift_days' must be an integer")

    action = payload.get("action")
    if action is not None and not isinstance(action, dict):
        raise ValidationError("Field 'action' must be an object")

    name_origin = payload.get("name_origin")
    name_count = payload.get("name_count")

    result = AnonymizeService.pseudonymize(
        text=text,
        group_overrides=group_overrides,
        date_shift_days=date_shift_days,
        action=action,
        name_origin=name_origin,
        name_count=name_count,
        engine=engine,
        llm_model=llm_model,
    )
    return jsonify({"success": True, **result})


@anonymize_bp.route("/pseudonymize-file", methods=["POST"])
@require_permission("feature:anonymize:view")
@handle_api_errors(logger_name="anonymize")
def anonymize_pseudonymize_file() -> Any:
    if "file" not in request.files:
        raise ValidationError("Missing file field 'file'")

    f = request.files["file"]
    filename = (f.filename or "").lower()
    file_bytes = f.read() or b""
    if not file_bytes:
        raise ValidationError("Uploaded file is empty")

    if filename.endswith(".docx"):
        text = _extract_text_from_docx(file_bytes)
    elif filename.endswith(".pdf"):
        text = _extract_text_from_pdf(file_bytes)
    else:
        raise ValidationError("Unsupported file type. Supported: .docx, .pdf")

    payload = request.form.to_dict() or {}

    engine = (payload.get("engine") or "offline").strip().lower()
    if engine not in {"offline", "llm", "hybrid"}:
        raise ValidationError("Invalid engine. Allowed: offline, llm, hybrid")
    llm_model = payload.get("llm_model") or None
    if isinstance(llm_model, str) and llm_model.strip():
        from db.models.llm_model import LLMModel
        db_model = LLMModel.get_by_model_id(llm_model.strip())
        if not db_model or not db_model.is_active or db_model.model_type != LLMModel.MODEL_TYPE_LLM:
            raise ValidationError("Selected llm_model is not an active LLM model")
        username = AuthUtils.extract_username_without_validation()
        if not LLMAccessService.user_can_access_model(username, llm_model.strip()):
            raise ForbiddenError("Selected llm_model is not available for this user")

    status_offline = AnonymizeService.quick_status()
    status_llm = AnonymizeService.llm_quick_status()
    if engine in {"offline", "hybrid"} and not status_offline.get("ready"):
        return jsonify({
            "success": False,
            "error": "Anonymize resources/models are not ready",
            "code": "ANONYMIZE_NOT_READY",
            "status": status_offline,
        }), 503
    if engine in {"llm", "hybrid"} and not status_llm.get("ready"):
        return jsonify({
            "success": False,
            "error": "LLM for anonymization is not configured/ready",
            "code": "ANONYMIZE_LLM_NOT_READY",
            "status": status_llm,
        }), 503

    # Optional JSON-like fields can be passed as plain strings; we keep it simple for now.
    # The frontend uses the JSON endpoint for interactive updates.
    date_shift_days = None
    if payload.get("date_shift_days"):
        try:
            date_shift_days = int(payload["date_shift_days"])
        except Exception:
            raise ValidationError("Invalid date_shift_days")

    result = AnonymizeService.pseudonymize(
        text=text,
        group_overrides={},
        date_shift_days=date_shift_days,
        action=None,
        name_origin=payload.get("name_origin") or None,
        name_count=int(payload["name_count"]) if payload.get("name_count") else None,
        engine=engine,
        llm_model=llm_model,
    )
    return jsonify({"success": True, **result})
