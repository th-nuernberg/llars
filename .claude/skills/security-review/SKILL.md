---
name: security-review
description: Perform security-focused code review checking for OWASP vulnerabilities, injection attacks, authentication issues, and security best practices. Use before deploying or when reviewing security-sensitive code.
---

# Security Review for LLARS

Perform a comprehensive security audit following OWASP guidelines and LLARS security standards.

## Security Review Scope

1. **Changed files** (default): Review git diff for security issues
2. **Specific routes**: Focus on API endpoints
3. **Full audit**: Scan entire codebase for vulnerability patterns

## OWASP Top 10 Checklist

### 1. Injection (SQL, Command, LDAP)

**Check for:**

```python
# VULNERABLE - SQL Injection
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)

# SAFE - Parameterized query
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# SAFE - SQLAlchemy ORM
User.query.filter_by(id=user_id).first()
```

```python
# VULNERABLE - Command Injection
os.system(f"convert {user_filename} output.png")
subprocess.run(f"grep {user_input} file.txt", shell=True)

# SAFE - Use array arguments, no shell=True
subprocess.run(["convert", validated_filename, "output.png"])
```

**Search patterns:**
```bash
# Find potential SQL injection
grep -rn "execute.*f\"" app/ --include="*.py"
grep -rn "execute.*%" app/ --include="*.py"

# Find potential command injection
grep -rn "os.system\|subprocess.*shell=True" app/ --include="*.py"
```

### 2. Broken Authentication

**Check for:**

```python
# REQUIRED on all protected routes
@authentik_required
@require_permission('feature:something:view')
def protected_route():
    user = g.authentik_user  # User object, not string!
    ...
```

**Verify:**
- [ ] All API routes have `@authentik_required`
- [ ] Permission checks with `@require_permission`
- [ ] Session tokens have expiration
- [ ] No hardcoded credentials in code
- [ ] Passwords not logged or returned in API responses

**Search for issues:**
```bash
# Find routes without auth decorators
grep -rn "^@bp.route\|^@app.route" app/routes/ --include="*.py" -A2 | grep -v authentik_required

# Find hardcoded credentials
grep -rni "password\s*=\s*['\"]" app/ --include="*.py" | grep -v "password_hash"
```

### 3. Sensitive Data Exposure

**Check for:**
- [ ] No secrets in code (API keys, passwords, tokens)
- [ ] Sensitive data not logged
- [ ] PII not exposed in API responses unnecessarily
- [ ] HTTPS enforced for sensitive operations

```python
# BAD - Logging sensitive data
logger.info(f"User login: {username}, password: {password}")

# BAD - Exposing sensitive fields
return jsonify(user.to_dict())  # Might include password_hash

# GOOD - Explicit field selection
return jsonify({
    'id': user.id,
    'username': user.username,
    'email': user.email
})
```

**Files to check:**
- `.env` files not committed
- `secrets.py`, `config.py` - no hardcoded values
- API responses - no sensitive data leakage

### 4. XML External Entities (XXE)

**Check for:**
```python
# VULNERABLE
from lxml import etree
tree = etree.parse(user_provided_xml)

# SAFE - Disable external entities
parser = etree.XMLParser(resolve_entities=False, no_network=True)
tree = etree.parse(user_provided_xml, parser)
```

### 5. Broken Access Control

**Check for:**
- [ ] Users can only access their own resources
- [ ] Role-based access properly enforced
- [ ] No IDOR (Insecure Direct Object Reference)

```python
# VULNERABLE - No ownership check
@bp.route('/documents/<int:doc_id>')
def get_document(doc_id):
    return Document.query.get(doc_id).to_dict()

# SAFE - Ownership verification
@bp.route('/documents/<int:doc_id>')
@authentik_required
def get_document(doc_id):
    user = g.authentik_user
    doc = Document.query.filter_by(id=doc_id, user_id=user.id).first()
    if not doc:
        raise NotFoundError('Document not found')
    return doc.to_dict()
```

### 6. Security Misconfiguration

**Check for:**
- [ ] Debug mode disabled in production
- [ ] Default credentials changed
- [ ] Error messages don't leak stack traces
- [ ] CORS properly configured

```python
# Check Flask config
app.config['DEBUG'] = False  # In production
app.config['TESTING'] = False

# CORS - Not too permissive
CORS(app, origins=['https://yourdomain.com'])  # Not origins='*'
```

### 7. Cross-Site Scripting (XSS)

**Check Vue templates:**
```vue
<!-- VULNERABLE - Raw HTML rendering -->
<div v-html="userInput"></div>

<!-- SAFE - Text interpolation (auto-escaped) -->
<div>{{ userInput }}</div>

<!-- VULNERABLE - Unescaped URL -->
<a :href="userUrl">Link</a>

<!-- SAFER - Validate URL scheme -->
<a :href="sanitizedUrl">Link</a>
```

**Backend API responses:**
```python
# Ensure Content-Type is set correctly
return jsonify(data)  # Sets application/json automatically

# Escape HTML if returning HTML
from markupsafe import escape
return escape(user_input)
```

### 8. Insecure Deserialization

**Check for:**
```python
# VULNERABLE - Pickle with untrusted data
import pickle
data = pickle.loads(user_provided_bytes)

# SAFE - Use JSON
import json
data = json.loads(user_provided_string)
```

### 9. Using Components with Known Vulnerabilities

**Check dependencies:**
```bash
# Python - Check for vulnerabilities
pip-audit

# Or with safety
pip install safety
safety check

# JavaScript - Check for vulnerabilities
cd llars-frontend
npm audit
```

### 10. Insufficient Logging & Monitoring

**Check for:**
- [ ] Authentication failures logged
- [ ] Access control failures logged
- [ ] Input validation failures logged
- [ ] No sensitive data in logs

```python
# GOOD - Logging security events
logger.warning(f"Failed login attempt for user: {username}")
logger.warning(f"Access denied: user {user_id} attempted to access resource {resource_id}")

# BAD - Logging sensitive data
logger.info(f"User {username} logged in with password {password}")
```

## LLARS-Specific Security Checks

### Authentication Flow
```python
# Every protected route MUST have:
@bp.route('/api/something')
@authentik_required           # 1. Authentication
@require_permission('...')    # 2. Authorization
@handle_api_errors(...)       # 3. Error handling (prevents info leakage)
def route():
    user = g.authentik_user   # 4. User from context (not from request!)
```

### File Uploads
```python
# Check file upload handlers for:
# 1. File type validation (not just extension)
# 2. File size limits
# 3. Secure filename generation
# 4. Storage outside web root

from werkzeug.utils import secure_filename
filename = secure_filename(file.filename)
```

### Database Queries
```python
# Always use SQLAlchemy ORM or parameterized queries
# NEVER string concatenation for queries

# Good
User.query.filter_by(email=email).first()

# Bad
db.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

## Security Report Format

```markdown
## Security Review Summary

**Risk Level**: Critical / High / Medium / Low / None

### Vulnerabilities Found

#### Critical
1. **[OWASP-A1]** SQL Injection in `app/routes/users.py:45`
   - **Impact**: Full database access
   - **Fix**: Use parameterized queries
   - **Code**: `query = f"SELECT * FROM users WHERE id = {id}"`

#### High
1. **[OWASP-A2]** Missing authentication on `/api/admin/users`
   - **Impact**: Unauthorized access to user data
   - **Fix**: Add `@authentik_required` decorator

#### Medium
1. **[OWASP-A6]** Debug mode enabled in production config

#### Low
1. **[OWASP-A10]** Insufficient logging for failed auth attempts

### Recommendations
1. Immediate action required for Critical issues
2. Schedule High issues for next sprint
3. Create tickets for Medium/Low issues

### Files Reviewed
- `app/routes/users.py` - 2 issues
- `app/routes/admin.py` - 1 issue

### Passed Checks
- [x] No hardcoded credentials
- [x] CORS properly configured
- [x] Dependencies up to date
```

## Quick Security Scan Commands

```bash
# Find routes without auth
grep -rn "@bp.route\|@app.route" app/routes/ -A3 | grep -B3 "def " | grep -v "authentik_required"

# Find potential SQL injection
grep -rn "execute.*f\"\|execute.*%" app/ --include="*.py"

# Find potential XSS in Vue
grep -rn "v-html" llars-frontend/src/ --include="*.vue"

# Find hardcoded secrets
grep -rni "api_key\|apikey\|secret\|password\s*=" app/ --include="*.py" | grep -v "__pycache__"

# Check for debug mode
grep -rn "DEBUG\s*=\s*True" app/ --include="*.py"

# Find .env files that shouldn't be committed
git ls-files | grep -E "\.env$|\.env\."
```

## Integration with CI/CD

LLARS CI/CD includes security scanning:
- `security:routes` - Checks all routes have proper auth
- `security:scan` - Runs automated security scanning

If this review finds issues, they should be fixed before the pipeline runs.
