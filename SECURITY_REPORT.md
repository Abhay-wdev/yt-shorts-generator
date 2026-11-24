# Security, Privacy & DRM Compliance Report

## Security Principles & Policies

This application processes user-owned media, handles OAuth credentials for Google accounts, and manages automated publishing workflows. Security and copyright safety are enforced by design.

---

## 1. Authentication & Token Protection

### Symmetric Encryption of OAuth Tokens
- All OAuth tokens (`access_token`, `refresh_token`, expiration timestamps) are encrypted before writing to SQLite using Fernet symmetric encryption (AES-128-CBC with PKCS7 padding and HMAC authentication).
- Encryption key is stored in `backend/.env` as `SECRET_KEY` and never hardcoded in source code or committed to git.
- Frontend never receives raw refresh tokens or client secrets. All token refresh operations happen server-side within `youtube_auth.py`.

### State Parameter Validation
- OAuth authorization requests generate a cryptographically random, timestamped `state` token using `secrets.token_urlsafe(32)`.
- The callback endpoint validates this state token against session cache to prevent Cross-Site Request Forgery (CSRF).

---

## 2. Ingestion Security & Path Traversal Prevention

### Safe File Path Handling
- Uploaded files are assigned a cryptographically secure UUID (`uuid.uuid4()`).
- File paths are normalized and resolved using `pathlib.Path.resolve()`.
- Access is restricted strictly to designated project subdirectories (`data/uploads/`, `data/proxies/`, `data/shorts/`). Any path attempting `../` traversal is rejected with a `400 Bad Request`.

### File Validation
- Uploaded media files are verified using `ffprobe` to ensure they contain valid video/audio streams and valid headers.
- Non-media payloads or executable files disguised as video are immediately blocked and quarantined.

---

## 3. Copyright & DRM Safety

### Source Permission Gate
Every source video record contains a `source_status` field:
- `owned`: Created and owned directly by the user.
- `licensed`: User possesses a commercial license.
- `authorized`: User has explicit permission from creator.
- `unknown`: Third-party or unidentified media.
- `restricted`: Protected or restricted material.

**Mandatory Enforcement**:
- Automated publishing (`AUTOMATIC` mode) is strictly forbidden for videos flagged as `unknown` or `restricted`.
- Only `owned` or explicitly `authorized` content can enter the publishing queue.
- The system does not implement DRM circumvention, private stream decryption, or YouTube access-control bypasses. Only authorized channels connected via official OAuth 2.0 or locally provided files are processed.
