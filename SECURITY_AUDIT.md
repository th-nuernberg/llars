# LLARS Security Audit Report

**Date:** February 2026
**Focus Areas:** Pickle deserialization, path traversal, file upload limits, CSRF protection

---

## 1. Pickle Deserialization Analysis

### Finding 1.1: Safe Pickle Usage (No User Input)

**Status:** ✅ SAFE

**Location:** `app/services/anonymize/anonymize_service.py`, lines 95-98

```python
@staticmethod
@lru_cache(maxsize=1)
def _load_recommender() -> tuple[Any, Any]:
    """Load the municipality recommender model (cached)."""
    paths = get_paths()
    with open(paths["recommender"], "rb") as f:
        recommender = pickle.load(f)  # Line 96
    with open(paths["scaler"], "rb") as f:
        scaler = pickle.load(f)  # Line 98
    return recommender, scaler
```

**Analysis:**
- Pickle files are loaded from **static, hard-coded paths** defined in `anonymize_paths.py`
- Paths come from environment variables with **safe defaults:**
  - `ANONYMIZE_MODEL_DIR` defaults to `{base}/models/anonymize`
  - `ANONYMIZE_DATA_DIR` defaults to `{base}/data/anonymize`
- Files are bundled with the application (not user-uploaded)
- The pickle files (`MuncipalityRecommender.sav`, `Scaler.sav`) are static ML models
- No user input influences the pickle file path or content

**Risk Level:** **LOW** - These are trusted, application-bundled files

**Recommendation:** No changes needed. Consider documenting pickle models as trusted sources.

---

## 2. Path Traversal Analysis

### Finding 2.1: Safe Path Construction in LaTeX Compilation

**Status:** ✅ SAFE

**Location:** `app/services/latex_compile_service.py`, lines 68-73

```python
def _safe_relative_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    normalized = os.path.normpath(normalized)
    if normalized.startswith("..") or os.path.isabs(normalized):
        raise LatexCompileError("Invalid path in workspace snapshot")
    return normalized
```

**How it's used:**
- **Line 145** (in `_materialize_snapshot`): Path from workspace snapshot is validated
  ```python
  rel_path = _safe_relative_path(path)  # Validates before use
  target_path = Path(base_dir) / rel_path
  ```

- **Line 231** (in `run_compile_job`): Main .tex file path is validated
  ```python
  rel_main = _safe_relative_path(main_path)  # Validates before use
  ```

- **Line 453-454** (in `synctex_forward_search`): Multiple path validations
  ```python
  rel_doc = _safe_relative_path(doc_path)      # Validates document path
  rel_main = _safe_relative_path(main_path)    # Validates main file path
  ```

**Security Analysis:**
1. **Normalization:** `os.path.normpath()` resolves `.` and `..` components
2. **Traversal Prevention:** Explicit check for `..` prefix and absolute paths
3. **Consistent Application:** Function is called before every path use (subprocess cwd, file I/O)
4. **Subprocess Safety:** Paths passed to `latexmk` and `synctex` commands are always validated

**Risk Level:** **MINIMAL** - Implementation is correct and comprehensive

**Edge Case to Monitor:**
- `_normalize_path()` (lines 294-300) is used for comparison but doesn't enforce traversal prevention
- This is used only for matching node paths in snapshots, not for file I/O, so it's safe
- Still, consider using `_safe_relative_path()` for consistency

---

## 3. File Upload Limits Analysis

### Finding 3.1: Inconsistent File Size Limits

**Status:** ⚠️ NEEDS REVIEW

#### Data Import Routes

**Location:** `app/routes/data_import/import_routes.py`, lines 77-78

```python
# Read content
content = file.read()  # Line 77 - NO SIZE CHECK
filename = file.filename
```

**Issue:**
- File is read entirely into memory **without size validation**
- `file_size=len(content)` is calculated **after** reading (line 83)
- File size check happens **after** memory allocation

**Risk:** Denial of Service via large file uploads
- Attacker could upload multi-GB files, exhausting server RAM
- Flask's default `MAX_CONTENT_LENGTH` is unlimited in this code

---

#### Document Upload Routes

**Location:** `app/routes/chatbot/chatbot_chat_routes.py`, line 22

```python
# Max file upload size (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024
```

Enforced at lines 59-60:
```python
if size > MAX_FILE_SIZE:
    raise ValueError(f'File {file.filename} exceeds max size of 10MB')
```

---

#### RAG Document Upload

**Location:** `app/services/rag/document_service.py`, line 31

```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
```

Enforced at lines 218-221:
```python
if file_size > MAX_FILE_SIZE:
    return {
        'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)} MB'
    }
```

Also enforced at lines 362-365.

---

#### Global Flask Configuration

**Location:** `app/main.py` - **NOT SET**

No global `MAX_CONTENT_LENGTH` configuration found. This means:
- Relies entirely on per-route checks
- Vulnerable routes could exhaust memory before checks run

---

### Recommendation: Implement Global File Size Limit

Add to `/Users/philippsteigerwald/PycharmProjects/llars/app/main.py` (after line 196):

```python
# Global file upload limit (prevents exhaustion before route validation)
# Set to largest needed: RAG documents = 50 MB
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB with buffer

# Optionally: Data import might need different limit
# but currently has NO limit - consider adding validation
```

**Fix for Data Import Route:**

In `/Users/philippsteigerwald/PycharmProjects/llars/app/routes/data_import/import_routes.py`,
replace lines 76-84 with:

```python
# Check file size before reading into memory
if request.content_length and request.content_length > 100 * 1024 * 1024:
    raise ValidationError("File exceeds 100 MB limit")

# Read content with streaming for large files
content = file.read()
if len(content) > 100 * 1024 * 1024:
    raise ValidationError("File exceeds 100 MB limit after decompression")

filename = file.filename
```

---

## 4. CSRF Protection Analysis

### Finding 4.1: No CSRF Protection Implemented

**Status:** ⚠️ REVIEW NEEDED

**Search Results:**
```bash
grep -r "WTF_CSRF|csrf_token|CSRFProtect|flask_wtf" --include="*.py"
# Result: Only in tests/conftest.py with 'WTF_CSRF_ENABLED': False
```

**Current State:**
- Flask-WTF is **NOT imported** in main application
- No CSRF middleware or decorators in any routes
- CSRF protection is **disabled in tests** (conftest.py: `'WTF_CSRF_ENABLED': False`)

**Why This Might Be Acceptable:**
1. **API-First Architecture:** LLARS is primarily a REST API (Vue + HTTP/JSON)
2. **Token-Based Auth:** Uses Authentik/JWT tokens, not session cookies
3. **SameSite Cookie Flag:** Not found in code but may be set by Authentik
4. **CORS Configuration:** Restrictive CORS settings (line 46 in main.py)

**Verification Needed:**

Check if Authentik session cookies have `SameSite=Strict`:
```bash
# In browser DevTools, check cookies for:
# - SameSite=Strict or SameSite=Lax (protects against CSRF)
# - Secure flag (only over HTTPS)
# - HttpOnly flag (prevents JS access)
```

**Risk Assessment:**

| Attack Vector | Risk | Reason |
|---|---|---|
| CSRF via form submission | LOW | No HTML forms, API-only |
| CSRF via fetch/XHR | LOW | CORS restrictions block cross-origin requests |
| CSRF via authenticated API calls | MEDIUM | If `Credentials: include` is used without proper protections |
| CSRF via WebSocket | LOW | Socket.IO has built-in protections |

**Recommendations:**

1. **Verify SameSite Cookie Enforcement**
   - Check Authentik configuration for `SameSite=Strict`
   - Update `.env` if needed: `AUTHENTIK_SECURE_COOKIES=True`

2. **Document CSRF Protection Strategy**
   - Add comment to `app/main.py` explaining why CSRF protection isn't needed:
     ```python
     # CSRF Protection Strategy:
     # - API-first architecture with token-based auth (Authentik/JWT)
     # - CORS restrictions prevent cross-origin attacks
     # - SameSite cookie flags enforce same-site request protection
     # - No HTML forms that could be exploited by CSRF
     ```

3. **Add Defense in Depth (Optional)**
   - Implement CSRF tokens for state-changing operations (POST/PUT/DELETE)
   - Use Flask-WTF or custom middleware if needed in future

4. **Monitor for Changes**
   - If adding traditional form submission, enable CSRF protection
   - If adding OAuth/federation flows, review CSRF implications

---

## 5. Summary Table

| Finding | Category | Severity | Status | Action |
|---------|----------|----------|--------|--------|
| **Pickle Files** | Deserialization | LOW | ✅ SAFE | None - document as trusted |
| **Path Traversal** | Path Validation | MINIMAL | ✅ SAFE | Monitor `_normalize_path()` for consistency |
| **File Upload Limits** | DoS Prevention | MEDIUM | ⚠️ NEEDS FIX | Add `MAX_CONTENT_LENGTH` to app config, validate data import |
| **CSRF Protection** | Session Security | LOW-MEDIUM | ⚠️ REVIEW | Verify SameSite cookies, document strategy |

---

## 6. Detailed Findings by File

### File: `app/services/anonymize/anonymize_service.py`

| Lines | Issue | Severity | Status |
|-------|-------|----------|--------|
| 95-98 | `pickle.load()` from static bundled files | NONE | ✅ SAFE |
| 129 | `pickle.load()` for recommender model | NONE | ✅ SAFE |

**Conclusion:** Pickle usage is safe; no user input influences pickle files.

---

### File: `app/services/latex_compile_service.py`

| Lines | Issue | Severity | Status |
|-------|-------|----------|--------|
| 68-73 | `_safe_relative_path()` validation function | NONE | ✅ SAFE |
| 145 | Path validation before file I/O | NONE | ✅ SAFE |
| 231 | Path validation before subprocess | NONE | ✅ SAFE |
| 453-454 | SyncTeX path validation | NONE | ✅ SAFE |
| 294-300 | `_normalize_path()` (comparison only) | MINIMAL | ✅ SAFE |

**Conclusion:** Path traversal protection is comprehensive and correctly applied.

---

### File: `app/routes/data_import/import_routes.py`

| Lines | Issue | Severity | Status |
|-------|-------|----------|--------|
| 77-78 | `file.read()` without size check | MEDIUM | ⚠️ NEEDS FIX |
| 83 | Size check happens **after** read | MEDIUM | ⚠️ NEEDS FIX |

**Issue:** No pre-validation of file size before reading into memory.

**Fix:**
```python
# Add before reading
if request.content_length and request.content_length > 100 * 1024 * 1024:
    raise ValidationError("File exceeds 100 MB")

content = file.read()
if len(content) > 100 * 1024 * 1024:
    raise ValidationError("File exceeds size limit after decompression")
```

---

### File: `app/main.py`

| Lines | Issue | Severity | Status |
|-------|-------|----------|--------|
| Not Set | Global `MAX_CONTENT_LENGTH` | MEDIUM | ⚠️ NEEDS FIX |
| 46 | CORS Configuration | LOW | ✅ SAFE |
| 169-189 | Secret Key Validation | LOW | ✅ SAFE |

**Fix:** Add global file size limit:
```python
# Add after CORS configuration (around line 50)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB
```

---

### File: `app/routes/chatbot/chatbot_chat_routes.py`

| Lines | Issue | Severity | Status |
|-------|-------|----------|--------|
| 22 | `MAX_FILE_SIZE = 10 * 1024 * 1024` | NONE | ✅ SAFE |
| 59-60 | File size validation | NONE | ✅ SAFE |

**Conclusion:** Proper file size limiting.

---

### File: `app/services/rag/document_service.py`

| Lines | Issue | Severity | Status |
|-------|-------|----------|--------|
| 31 | `MAX_FILE_SIZE = 50 * 1024 * 1024` | NONE | ✅ SAFE |
| 218-221 | Size validation with user feedback | NONE | ✅ SAFE |
| 362-365 | Duplicate size validation | NONE | ✅ SAFE |

**Conclusion:** Proper file size limiting with good error messages.

---

### CSRF Protection - All Routes

| Finding | Severity | Status |
|---------|----------|--------|
| No Flask-WTF implementation | LOW-MEDIUM | ⚠️ REVIEW |
| No CSRF token validation | LOW-MEDIUM | ⚠️ REVIEW |
| API-first design mitigates risk | MITIGATING | ✅ DESIGN STRENGTH |

**Next Steps:** Verify Authentik SameSite cookie configuration.

---

## 7. Quick Fixes Checklist

### Priority 1: File Upload Limit
- [ ] Add `app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024` to `app/main.py` (after line 50)
- [ ] Add pre-read validation to `app/routes/data_import/import_routes.py` (around line 77)
- [ ] Test with > 100 MB file upload

### Priority 2: CSRF Strategy Documentation
- [ ] Verify Authentik SameSite cookie settings
- [ ] Document CSRF protection strategy in `app/main.py`
- [ ] Consider adding CSRF tokens if forms are added in future

### Priority 3: Path Validation Consistency
- [ ] Consider using `_safe_relative_path()` in `_normalize_path()` comparison
- [ ] Add comment explaining why comparison function is different

---

## 8. Testing Recommendations

```bash
# Test file upload size limit
curl -X POST \
  -F "file=@large_file.bin" \
  http://localhost:55080/api/import/upload \
  -H "Authorization: Bearer <token>"

# Test path traversal (should fail)
# Attempt to access snapshot with path="../../../etc/passwd"

# Verify pickle safety
# Confirm no user-controlled input affects pickle file paths
```

---

## Conclusion

**Overall Security Posture:** ✅ GOOD

**Key Strengths:**
- Pickle usage is safe (bundled files only)
- Path traversal protection is comprehensive
- Most routes implement proper file size limits
- Authentication is delegated to Authentik (reduces attack surface)

**Areas for Improvement:**
- Global `MAX_CONTENT_LENGTH` limit needed (1 fix)
- Data import route lacks pre-read size validation (1 fix)
- CSRF strategy should be documented (documentation only)

**Estimated Effort:** 15-30 minutes to implement all fixes

---

**Report prepared:** February 2026
**Codebase version:** LLARS 3.0
