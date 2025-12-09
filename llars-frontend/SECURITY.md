# Security Best Practices - LLARS Frontend

## XSS (Cross-Site Scripting) Protection

### Overview
All user-generated content and dynamic HTML is sanitized using **DOMPurify** to prevent XSS attacks.

### Implementation

#### Sanitization Utility
Location: `src/utils/sanitize.js`

Provides the following functions:
- `sanitizeHtml(html)` - Sanitizes HTML with safe defaults
- `sanitizeHtmlCustom(html, config)` - Custom sanitization configuration
- `sanitizeText(text)` - Converts newlines to `<br>` and sanitizes
- `stripHtml(html)` - Strips all HTML tags

#### Protected Components

**1. RankerDetail.vue** (app/routes/keycloak_routes.py:27,28,56,57,85,86,115,116)
- **Vulnerability**: `v-html="formatFeatureContent()"` used to display user-generated feature content
- **Fix**: All content sanitized through `sanitizeHtml()` before rendering
- **Risk**: High - displays JSON content that could contain malicious scripts

**2. TestPromptDialog.vue** (app/routes/keycloak_routes.py:33)
- **Vulnerability**: `v-html="promptHighlighted"` for syntax highlighting
- **Fix**: Replaced manual HTML escaping with DOMPurify sanitization
- **Risk**: Medium - displays prompts that could contain user input

**3. HistoryGenerationDetail.vue** (app/routes/keycloak_routes.py:20)
- **Status**: ✅ Already protected
- **Implementation**: Uses `formatContent()` with DOMPurify sanitization
- **Risk**: High - displays message content from database

### Usage Guidelines

#### DO ✅
```vue
<script setup>
import { sanitizeHtml } from '@/utils/sanitize';

const content = ref(userGeneratedHTML);
const safeContent = computed(() => sanitizeHtml(content.value));
</script>

<template>
  <div v-html="safeContent"></div>
</template>
```

#### DON'T ❌
```vue
<!-- NEVER do this with user content! -->
<template>
  <div v-html="userGeneratedHTML"></div>
</template>
```

### Allowed HTML Tags
By default, `sanitizeHtml()` allows:
- Formatting: `<p>`, `<br>`, `<strong>`, `<em>`, `<u>`, `<span>`, `<div>`
- Lists: `<ul>`, `<ol>`, `<li>`
- Links: `<a>` (only with `href` attribute)

All scripts, event handlers, and dangerous tags are removed.

### Testing XSS Protection

Test vectors to verify protection:
```javascript
// Should be stripped
'<script>alert("XSS")</script>'
'<img src=x onerror=alert("XSS")>'
'<a href="javascript:alert(1)">Click</a>'

// Should be preserved (safe formatting)
'<p>Hello <strong>World</strong></p>'
'Line 1<br>Line 2'
'<a href="https://example.com">Link</a>'
```

## Content Security Policy (CSP)

**TODO**: Implement CSP headers in nginx configuration to provide defense-in-depth:

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self' ws: wss:; frame-ancestors 'none';";
```

## Additional Security Measures

### 1. Authentik Authentication
Alle API-Endpunkte sind per JWT abgesichert, validiert über Authentik (OIDC).

### 2. Rate Limiting
Flask-Limiter configured with:
- 200 requests per day (default)
- 50 requests per hour (default)
- Endpoint-specific limits for sensitive operations

### 3. CORS Configuration
Restricted to allowed origins from environment variables (production mode).

### 4. Input Validation
- All API inputs validated server-side
- Type checking enforced
- Length limits on text fields

## Vulnerability Reporting

If you discover a security vulnerability, please report it to the development team immediately.

**DO NOT** create public GitHub issues for security vulnerabilities.

## References

- [DOMPurify Documentation](https://github.com/cure53/DOMPurify)
- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [Content Security Policy Reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
