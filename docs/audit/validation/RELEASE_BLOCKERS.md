# Release Blockers

**Project:** Global Airdrop Hunter  
**Date:** 2026-11-13  
**Auditor:** Kilo (Second-Pass Validation)  
**Classification System:** CRITICAL / HIGH / MEDIUM / LOW

---

## Classification Definitions

### CRITICAL - Application Cannot Function

- Application crashes on startup
- Core features completely broken
- Security vulnerabilities with active exploits
- Data loss or corruption possible
- **Must fix before ANY release**

### HIGH - Major Feature Broken

- Important features non-functional
- Significant user impact
- Workaround exists but poor
- **Must fix before production release**

### MEDIUM - Feature Degraded

- Feature works but with limitations
- User experience impacted
- Technical debt accumulating
- **Should fix before production, can defer if needed**

### LOW - Minor Issue

- Cosmetic issues
- Documentation gaps
- Nice-to-have improvements
- **Can defer indefinitely**

---

## CRITICAL Blockers

### C1: Electron Application Cannot Start

**Severity:** CRITICAL  
**Status:** CONFIRMED  
**Release Blocker:** YES - Absolute blocker

**Description:**

The Electron main process crashes immediately on startup due to undefined `crypto` object.

**Location:** `desktop/main.js:13`

**Evidence:**

```javascript
function generateToken() {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);  // ReferenceError: crypto is not defined
  return Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
}
```

**Root Cause:**

- `crypto` is used without being imported
- Node.js requires explicit `const crypto = require('crypto');`

**Impact:**

- Electron app cannot start at all
- No desktop functionality accessible
- Only browser-based workaround (`launch.ps1`) works

**Reproduction:**

1. Run `npm run dev` or `npm start`
2. Application crashes with ReferenceError

**Fix:**

```javascript
const crypto = require('crypto');  // Add at top of desktop/main.js
```

**Estimated Fix Time:** 1 minute

**Verification After Fix:**

1. Electron app starts successfully
2. Token generation works
3. Backend spawns correctly

---

### C2: Campaign API Broken in Frontend

**Severity:** CRITICAL  
**Status:** CONFIRMED  
**Release Blocker:** YES - Core feature broken

**Description:**

Duplicate `campaigns` object in preload.js causes JavaScript object property overwrite, losing `list()` and `get()` methods.

**Location:** `desktop/preload.js:50-75`

**Evidence:**

```javascript
// First definition (lines 50-62)
campaigns: {
  list: (params = {}) => { /* ... */ },
  get: (id) => this.request(`/api/v1/campaigns/${encodeURIComponent(id)}`),
},

// ... other code ...

// Second definition (lines 71-75) - OVERWRITES FIRST
campaigns: {
  save: (id) => this.request(`/api/v1/campaigns/${encodeURIComponent(id)}/save`, {
    method: 'POST',
  }),
},
```

**Root Cause:**

- JavaScript object literal with duplicate property names
- Last property wins, first is completely overwritten
- `campaigns.list()` and `campaigns.get()` no longer exist

**Impact:**

- Frontend cannot load campaign list
- Frontend cannot load campaign details
- Campaign browsing completely broken
- Only `campaigns.save()` works

**User Impact:**

- Dashboard shows no campaigns
- Campaigns page is empty
- Cannot search or filter campaigns
- Core feature of the application is non-functional

**Reproduction:**

1. Start application (even in browser mode)
2. Navigate to Campaigns section
3. Frontend calls `window.api.campaigns.list()`
4. Error: `campaigns.list is not a function`

**Fix:**

```javascript
campaigns: {
  list: (params = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const query = searchParams.toString();
    return this.request(`/api/v1/campaigns${query ? `?${query}` : ''}`);
  },
  get: (id) => this.request(`/api/v1/campaigns/${encodeURIComponent(id)}`),
  save: (id) => this.request(`/api/v1/campaigns/${encodeURIComponent(id)}/save`, {
    method: 'POST',
  }),
},
```

**Estimated Fix Time:** 5 minutes

**Verification After Fix:**

1. Campaign list loads in frontend
2. Campaign details display correctly
3. Campaign search works
4. Campaign save still works

---

### C3: Desktop-Backend Authentication Failure

**Severity:** CRITICAL  
**Status:** CONFIRMED  
**Release Blocker:** YES - Desktop-backend communication broken

**Description:**

Electron and backend generate independent tokens, causing authentication to fail for all API requests.

**Locations:**

- `desktop/main.js:11-15` (generateToken function)
- `desktop/main.js:46` (apiToken = generateToken())
- `desktop/main.js:50` (LOCAL_API_TOKEN: apiToken passed to backend)
- `backend/main.py:28-30` (token_manager.generate() ignores passed token)

**Evidence:**

**Electron side:**

```javascript
// Line 46: Generate token
apiToken = generateToken();

// Line 50: Pass to backend
const env = {
  ...process.env,
  LOCAL_API_TOKEN: apiToken,
};
```

**Backend side:**

```python
# Line 28-30: Generate DIFFERENT token
api_token = token_manager.generate()  # Creates new random token
logger.info(f"API Token generated: {api_token}")
os.environ["LOCAL_API_TOKEN"] = api_token  # Overwrites env var
```

**Root Cause:**

- Electron generates token BEFORE spawning backend
- Backend ignores the passed token and generates its own
- Two different tokens exist
- Auth middleware validates against backend's token, not Electron's

**Impact:**

- All API requests from desktop fail with 401 Unauthorized
- Desktop cannot communicate with backend
- No data can be fetched or saved
- Application is completely non-functional

**User Impact:**

- Dashboard shows no data
- All API calls fail
- Application appears broken

**Reproduction:**

1. Start Electron app
2. Desktop tries to call `GET /api/v1/health`
3. Request includes `X-Local-API-Token: <electron_token>`
4. Backend validates against `<backend_token>`
5. Response: `401 Unauthorized`

**Fix Options:**

**Option A: Backend reads token from env (simpler)**

```python
# In backend/main.py lifespan
api_token = os.environ.get("LOCAL_API_TOKEN")
if not api_token:
    api_token = token_manager.generate()
    logger.info(f"API Token generated: {api_token}")
else:
    token_manager._token = api_token
    token_manager._token_hash = create_token_hash(api_token)
    logger.info(f"API Token received from parent: {api_token[:8]}...")
```

**Option B: Backend generates, Electron reads via IPC (more secure)**

```python
# In backend/main.py lifespan - generate token
api_token = token_manager.generate()
logger.info(f"API Token generated: {api_token}")

# In desktop/main.js - don't generate, read from backend
// Remove generateToken() call
// Add IPC handler to fetch token from backend health endpoint
```

**Recommended:** Option A (simpler, faster to implement)

**Estimated Fix Time:** 15 minutes

**Verification After Fix:**

1. Desktop starts backend with token in env
2. Backend uses the provided token
3. Desktop API calls succeed
4. Health check returns 200 OK
5. Dashboard loads data

---

## HIGH Blockers

### H1: No Automated Tests

**Severity:** HIGH  
**Status:** CONFIRMED  
**Release Blocker:** YES for production, NO for initial release

**Description:**

Zero test coverage across entire codebase.

**Evidence:**

- `tests/` directory is empty
- No pytest configuration
- No test framework installed
- No CI/CD pipeline

**Impact:**

- No regression protection
- Bugs can be introduced undetected
- Cannot safely refactor code
- No confidence in changes
- Cannot verify fixes don't break existing functionality

**Risk:**

- High probability of bugs in production
- Manual testing only
- Time-consuming verification process

**Recommendation:**

1. Add pytest with basic fixtures
2. Write API smoke tests
3. Test database migrations
4. Test auth flow
5. Add CI pipeline

**Estimated Effort:** 2-3 days

---

### H2: Discovery Feature Incomplete

**Severity:** HIGH  
**Status:** CONFIRMED  
**Release Blocker:** YES for feature completeness

**Description:**

4 of 7 required platform adapters implemented. Missing Galxe and Layer3 adapters.

**Evidence:**

- ✅ CoinGecko adapter
- ✅ DefiLlama adapter
- ✅ GitHub adapter
- ✅ RSS adapter
- ❌ Galxe adapter (not implemented)
- ❌ Layer3 adapter (not implemented)

**Impact:**

- Discovery works but limited to generic crypto data
- Cannot discover campaigns from primary airdrop platforms
- Core feature is incomplete

**User Impact:**

- Users miss campaigns from major platforms
- Reduces usefulness of the application

**Recommendation:**

1. Implement Galxe adapter (2-3 hours)
2. Implement Layer3 adapter (2-3 hours)
3. Test with real API calls

**Estimated Effort:** 1-2 days

---

### H3: Electron Packaging Blocked

**Severity:** HIGH  
**Status:** CONFIRMED  
**Release Blocker:** YES for traditional distribution

**Description:**

Cannot build Windows installer due to electron-builder issues.

**Evidence:**

- `ELECTRON_INTEGRATION_ISSUES.md` documents the problem
- Phase 9 marked as "BLOCKED"
- No installer artifacts can be created

**Root Cause:**

- electron-builder file locking on Windows
- Electron module loading issues
- Postinstall scripts fail

**Impact:**

- Cannot distribute as traditional Windows desktop app
- Browser launcher workaround exists but not ideal
- No installer for end users

**Workaround:**

- `scripts/launch.ps1` opens app in Edge `--app` mode
- Functional but not a true desktop app

**Recommendation:**

1. Debug electron-builder configuration
2. Try different build approaches (asar: false, different targets)
3. Consider alternative packagers
4. Commit to browser-based distribution if unresolvable

**Estimated Effort:** 1-2 days

---

## MEDIUM Issues

### M1: Migration Schema Duplication

**Severity:** MEDIUM  
**Status:** CONFIRMED  
**Release Blocker:** NO

**Description:**

Migrations 002 and 005 both create `risk_rules` table with different schemas.

**Location:** `backend/database/migrations/002_*.sql` and `005_*.sql`

**Impact:**

- Could cause conflicts on clean install
- Migration might fail or create duplicate table
- Schema inconsistency risk

**Recommendation:**

1. Review both migrations
2. Consolidate into single migration
3. Test clean install

**Estimated Effort:** 2-4 hours

---

### M2: No Migration Runner

**Severity:** MEDIUM  
**Status:** CONFIRMED  
**Release Blocker:** NO (but required for production)

**Description:**

`run_migrations()` is called in `backend/main.py:27` but implementation not found.

**Evidence:**

```python
# Line 27
run_migrations()
```

**But:**

- No `run_migrations()` function found in codebase
- Migrations are SQL files only
- No Python code to apply them

**Impact:**

- Database setup requires manual migration application
- Not user-friendly
- Could cause startup failures if migrations not applied

**Recommendation:**

1. Implement `run_migrations()` function
2. Track applied migrations in `schema_migrations` table
3. Auto-apply on startup
4. Test clean install

**Estimated Effort:** 4-6 hours

---

### M3: Frontend Component Architecture Missing

**Severity:** MEDIUM  
**Status:** CONFIRMED  
**Release Blocker:** NO

**Description:**

No component architecture. All UI code in monolithic `app.js`.

**Location:** `frontend/js/app.js`

**Impact:**

- Poor maintainability
- No code reusability
- Difficult to test
- Hard to add new features

**Recommendation:**

1. Create component directory structure
2. Extract reusable components
3. Implement component lifecycle
4. Add component tests

**Estimated Effort:** 3-5 days (can be deferred)

---

### M4: No OpenAPI Documentation

**Severity:** MEDIUM  
**Status:** CONFIRMED  
**Release Blocker:** NO

**Description:**

FastAPI app exists but OpenAPI docs not verified working.

**Location:** `backend/main.py:49-50`

**Evidence:**

```python
docs_url="/docs",
redoc_url="/redoc",
```

**Impact:**

- API documentation not verified
- Cannot confirm Swagger UI works
- Developer experience reduced

**Recommendation:**

1. Verify `/docs` endpoint works
2. Test OpenAPI schema generation
3. Add API examples

**Estimated Effort:** 1-2 hours

---

## LOW Issues

### L1: No Code Comments

**Severity:** LOW  
**Status:** CONFIRMED  
**Release Blocker:** NO

**Description:**

No comments in source code (per project convention).

**Impact:**

- Reduced maintainability
- Harder for new developers
- But consistent with project style

**Recommendation:**

- Keep as-is (project convention)
- Add docstrings for public APIs only

---

### L2: Dependency Audit Not Automated

**Severity:** LOW  
**Status:** CONFIRMED  
**Release Blocker:** NO

**Description:**

No automated dependency vulnerability scanning.

**Recommendation:**

1. Add `pip-audit` to requirements
2. Add `npm audit` to build process
3. Schedule regular scans

**Estimated Effort:** 2-4 hours

---

## Blocker Summary

| ID | Issue | Severity | Release Blocker | Fix Time |
| -- | ----- | -------- | --------------- | -------- |
| C1 | Electron crypto undefined | CRITICAL | YES | 1 min |
| C2 | Duplicate campaigns object | CRITICAL | YES | 5 min |
| C3 | Token mismatch | CRITICAL | YES | 15 min |
| H1 | No automated tests | HIGH | YES (prod) | 2-3 days |
| H2 | Discovery incomplete | HIGH | YES (feature) | 1-2 days |
| H3 | Packaging blocked | HIGH | YES (deploy) | 1-2 days |
| M1 | Migration duplication | MEDIUM | NO | 2-4 hrs |
| M2 | No migration runner | MEDIUM | NO | 4-6 hrs |
| M3 | No components | MEDIUM | NO | 3-5 days |
| M4 | No OpenAPI docs | MEDIUM | NO | 1-2 hrs |
| L1 | No comments | LOW | NO | N/A |
| L2 | No dep audit | LOW | NO | 2-4 hrs |

---

## Critical Path to Release

### Phase 1: Fix Critical Bugs (30 minutes)

1. ✅ Fix crypto import (1 min)
2. ✅ Fix duplicate campaigns (5 min)
3. ✅ Fix token mismatch (15 min)
4. ✅ Verify Electron starts (10 min)

**Milestone:** Application can start and basic communication works

### Phase 2: Verify Core Features (1 day)

1. Test campaign CRUD end-to-end
2. Test discovery with real adapters
3. Test eligibility tracking
4. Test risk assessment

**Milestone:** Core features verified working

### Phase 3: Complete Discovery (1-2 days)

1. Implement Galxe adapter
2. Implement Layer3 adapter
3. Test all adapters

**Milestone:** Discovery feature complete

### Phase 4: Add Basic Tests (2-3 days)

1. Set up pytest
2. Write API smoke tests
3. Test database migrations
4. Add CI pipeline

**Milestone:** Basic test coverage achieved

### Phase 5: Resolve Packaging (1-2 days)

1. Debug electron-builder
2. Create installer
3. Test clean install

**Milestone:** Distributable installer created

---

## Release Readiness Checklist

### Must Have (Blockers)

- [ ] C1: Electron starts successfully
- [ ] C2: Campaign API works in frontend
- [ ] C3: Desktop-backend auth works
- [ ] H1: Basic test suite exists
- [ ] H2: All required adapters implemented
- [ ] H3: Installer can be built (or browser launcher accepted)

### Should Have (High Priority)

- [ ] M1: Migrations consolidated
- [ ] M2: Migration runner implemented
- [ ] M4: OpenAPI docs verified

### Nice to Have (Medium Priority)

- [ ] M3: Component architecture
- [ ] L2: Dependency scanning automated

---

## Conclusion

**6 release blockers identified:**

1. **3 CRITICAL bugs** prevent application from starting (fixable in 30 minutes)
2. **3 HIGH priority gaps** prevent production release (fixable in 4-7 days)

**Total estimated effort to production-ready:** 7-10 days

**Immediate action:** Fix the 3 CRITICAL bugs to achieve basic functionality.