# Global Airdrop Hunter - Security Documentation

## Security Model

### Threat Model

**Assets Protected**:
- User campaign data (tracking, notes, claims)
- Local SQLite database
- API authentication tokens
- Source discovery configuration

**Threat Actors**:
- Malicious websites/campaign content
- Compromised discovery sources
- Local malware on user machine
- Network attackers (MITM on localhost)

**Trust Boundaries**:
1. **Renderer Process** (untrusted) ↔ **Main Process** (trusted) via IPC
2. **Frontend** ↔ **Backend API** (trusted, localhost only)
3. **Backend** ↔ **External Sources** (untrusted, validated)
4. **Application** ↔ **File System** (user data only)

### Security Controls

#### Electron Hardening
| Control | Implementation | Status |
|---------|---------------|--------|
| Context Isolation | `contextIsolation: true` | ✅ Enabled |
| Node Integration | `nodeIntegration: false` | ✅ Disabled |
| Sandbox | `sandbox: true` | ✅ Enabled |
| Web Security | `webSecurity: true` | ✅ Enabled |
| Allow Running Insecure Content | `allowRunningInsecureContent: false` | ✅ Disabled |
| Experimental Features | `experimentalFeatures: false` | ✅ Disabled |
| Spellcheck | `spellcheck: false` | ✅ Disabled |

#### Content Security Policy
Injected via `webRequest.onHeadersReceived`:
```
default-src 'self';
script-src 'self';
style-src 'self' 'unsafe-inline';
img-src 'self' data:;
font-src 'self';
connect-src 'self' http://127.0.0.1:*;
frame-src 'none';
object-src 'none';
base-uri 'self';
form-action 'self';
```

Additional headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`

#### IPC Allowlist
Only these channels exposed via `contextBridge`:
- `get-api-config` - Returns backend URL + token
- `open-external` - Validates URL, opens in default browser
- `get-app-version` - Returns Electron app version

Renderer cannot directly call `ipcRenderer.invoke()` on arbitrary channels.

#### Window Security
- `setWindowOpenHandler` - All external links open in default browser
- `will-navigate` handler - Prevents navigation away from `file://` or `http://127.0.0.1:`

### API Security

#### Authentication
- **Method**: Bearer token via `X-Local-API-Token` header
- **Token**: 32-byte cryptographically random (hex-encoded)
- **Generation**: At backend startup, logged to console
- **Storage**: In memory only, regenerated on restart
- **Validation**: Constant-time comparison (hmac.compare_digest)

#### Authorization
- All endpoints (except `/health`, `/docs`, `/redoc`, `/openapi.json`) require valid token
- Origin validation: Only `http://127.0.0.1:*`, `http://localhost:*`, `file://` allowed
- Request size limit: 1 MB (413 Payload Too Large for oversized)

#### Input Validation
- All endpoints use Pydantic models for request/response validation
- SQL injection prevention via parameterized queries
- XSS prevention: JSON responses escape HTML characters
- Path traversal prevention: Path validation for file operations

### Data Protection

#### Local Storage
- Database: `%LOCALAPPDATA%\GlobalAirdropHunter\app.db` (SQLite)
- Backups: `%LOCALAPPDATA%\GlobalAirdropHunter\backups\`
- Logs: `%LOCALAPPDATA%\GlobalAirdropHunter\logs\`
- No cloud sync, no telemetry, no external data transmission

#### Sensitive Data Handling
- **No wallet connections** - No private keys, seed phrases, or signing
- **No credentials stored** - API tokens for external sources in config only
- **No PII collected** - Campaign data only
- **Tokens** - Generated at runtime, not persisted

#### Backup Security
- Timestamped backups with integrity verification (PRAGMA integrity_check)
- Restore creates pre-restore backup automatically
- Integrity check on restore (PRAGMA integrity_check)

### External Source Security

#### Source Discovery
- Only documented public APIs used
- Respects `robots.txt` and rate limits
- No scraping bypassing authentication/CAPTCHA
- Source health checks before each scan

#### Content Processing
- All external content treated as untrusted
- HTML sanitized before storage
- URLs validated and normalized
- Content hashes stored for deduplication
- Maximum response size limits per adapter

#### Risk Assessment
- 15 built-in risk rules across 6 categories
- Critical overrides: credential requests, upfront payments
- Findings stored with rule version, evidence, matched content
- Critical overrides override score regardless of weight

### Network Security

#### Network Binding
- Backend binds to `127.0.0.1:8000` only
- No external network exposure
- No UPnP, no port forwarding

#### TLS/SSL
- Not applicable (localhost only)
- No certificate management needed
- Self-signed certificates not used

### Dependency Security

#### Supply Chain
- Dependencies pinned to specific versions
- `npm audit` and `pip-audit` in CI pipeline
- Vulnerable dependencies updated promptly
- Electron version pinned (28.3.3)

#### Known Vulnerabilities (Accepted)
| Package | Version | Vulnerability | Status |
|---------|---------|---------------|--------|
| electron-builder | 24.13.3 | devDependencies only | Accepted (build only) |
| starlette | 0.35.1 | Transitive from fastapi | Monitor |
| pytest | 8.3.5 | Test dependency only | Accepted (test only) |

### Incident Response

#### Compromise Indicators
- Unexpected network connections
- Unauthorized database modifications
- Unexpected process spawns
- Token reuse across sessions

#### Response Procedures
1. **Isolate**: Kill electron/node processes
2. **Preserve**: Copy database and logs to safe location
3. **Analyze**: Check logs, database integrity, running processes
4. **Remediate**: Restore from verified backup if needed
5. **Report**: Document findings, update security controls

### Compliance

#### Data Privacy
- No personal data collected
- No analytics, no tracking
- GDPR/CCPA not applicable (no PII)
- User controls all data locally

#### Financial Regulations
- No financial advice provided
- No wallet connections or transactions
- Educational/informational only
- Disclaimer: Not financial advice

### Security Checklist (Pre-Release)

- [x] Electron context isolation enabled
- [x] Electron sandbox enabled
- [x] Node integration disabled
- [x] CSP headers configured
- [x] IPC allowlist configured
- [x] Window open/navigation handlers
- [x] API token authentication
- [x] Origin validation
- [x] Request size limits
- [x] Input validation (Pydantic)
- [x] SQL parameterization
- [x] CSP headers on all responses
- [x] XSS prevention (JSON escaping)
- [x] Request size limit (1MB)
- [x] Origin validation (localhost only)
- [x] Backup/restore with integrity checks
- [x] Dependency vulnerability scans
- [x] No hardcoded secrets
- [x] No wallet connections
- [x] No private key handling

### Residual Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Electron module loading issue on Windows | High | Medium | Browser launcher fallback |
| electron-builder file locking | High | Low | Documented workaround |
| Source API changes | Medium | Medium | Adapter pattern, health checks |
| Malicious campaign content | Low | High | Strict content handling, risk engine |
| Database corruption | Low | High | Migrations, verified backups |
| Scope creep | Medium | Low | Phase gates, wallet claiming out of scope |

### Security Testing

#### Automated
- `npm audit` - Node.js dependencies
- `pip-audit` - Python dependencies
- ESLint (if configured) - JavaScript static analysis
- Bandit (if configured) - Python static analysis

#### Manual
- Penetration testing of API endpoints
- CSP bypass attempts
- IPC channel fuzzing
- Origin header manipulation
- Oversized payload testing
- Malformed JSON handling
- SQL injection attempts
- XSS payload injection

#### Penetration Testing Scenarios
1. Token brute force (rate limiting not implemented - local only)
2. Origin header spoofing (blocked by middleware)
3. Path traversal in file operations (validated)
4. SQL injection in search/filter (parameterized)
5. XSS in campaign data (escaped in JSON)
6. SSRF via campaign URLs (validated, localhost only)
7. IPC channel escape (allowlist enforced)

### Security Contacts

For security issues:
- Document findings with reproduction steps
- Include logs, screenshots, environment details
- No public disclosure until remediation

---

*Security Document Version: 1.0.0*
*Last Updated: 2026-11-13*
*Review Cycle: Per release*