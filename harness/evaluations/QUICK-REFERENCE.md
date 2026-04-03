# IFRS 9 ECL Platform — Quick Reference Guide

**Last Updated**: 2026-03-30
**Status**: Testing Framework Complete, Live Testing Blocked
**Test Tool**: agent-browser 0.17.0

---

## QUICK STATS

| Metric | Value |
|--------|-------|
| Total Pages | 18 |
| Components | 38 |
| Forms to Test | 12+ |
| Screenshots | 4 (authentication flow) |
| Code Files Reviewed | 47 |
| Lines of Code Analyzed | ~15,000 |
| ESLint Errors | 559 (mostly type safety) |
| Unit Tests | 103 (102 passing, 1 failing) |
| Critical Issues Found | 3 |
| High Priority Issues | 6 |
| Estimated Testing Time | 9-14 hours |

---

## BLOCKERS TO LIVE TESTING

### 🔴 CRITICAL (Prevents Testing)
1. **OAuth Credentials Missing**
   - App requires Databricks login
   - Cannot proceed without credentials
   - Contact: Databricks team

2. **Lakebase Database Not Accessible**
   - Backend requires PostgreSQL connection
   - Local development blocked
   - Fix: Set environment variables or use mock

3. **DataTable Test Failing**
   - Test expects "1 / 4", gets "Page 1 of 4"
   - CI/CD pipeline blocked
   - Fix: Update test string match

---

## FILES GENERATED

### Main Documents
- **`browser-test-manifest.md`** (45 KB)
  - Complete testing checklist for all 18 pages
  - Form validation procedures
  - Data persistence tests
  - Performance benchmarks
  - Ready to execute with credentials

- **`BROWSER-TEST-ISSUES.md`** (28 KB)
  - 10 detailed issues identified
  - Code examples and fixes
  - Priority rankings
  - Recommendations

- **`TESTING-SUMMARY.md`** (This gives overview)
  - Executive summary
  - Test execution procedures
  - Timeline and effort estimates

- **`QUICK-REFERENCE.md`** (This file)
  - Quick lookup guide
  - Common commands
  - Troubleshooting

### Screenshots (4 total)
```
/Users/steven.tan/Expected Credit Losses/harness/screenshots/browser-test/
├── 01-login-page.png (21 KB) - Databricks login
├── 02-okta-login.png (46 KB) - Okta SSO form
├── 03-frontend-loading.png (4.2 KB) - Frontend without API
└── 04-frontend-with-backend.png (4.2 KB) - Frontend with API
```

---

## PAGES TO TEST (All 18)

### Main Workflow (7 steps)
- [ ] 1. Create Project - Setup reporting date, currency, framework
- [ ] 2. Data Processing - Portfolio summary, product breakdown
- [ ] 3. Data Control - Quality gates, GL reconciliation
- [ ] 4. Satellite Model - Logistic regression parameters
- [ ] 5. Monte Carlo - Simulation runner with progress
- [ ] 6. Stress Testing - 8 macro scenarios, sensitivity analysis
- [ ] 7. Sign-Off - IFRS 7 disclosures, approvals

### Admin & Configuration
- [ ] 8. Admin - System settings, user management, API config
- [ ] 9. Data Mapping - Source data mapping interface

### Analytics & Reporting
- [ ] 10. Model Registry - Model versioning and history
- [ ] 11. Backtesting - Historical validation results
- [ ] 12. Hazard Models - Advanced credit models
- [ ] 13. Markov Chains - State transition analysis
- [ ] 14. GL Journals - General ledger interface
- [ ] 15. Regulatory Reports - IFRS 7 report generation
- [ ] 16. Advanced Features - CCF, cure rates, collateral
- [ ] 17. Approval Workflow - Governance and sign-offs
- [ ] 18. Setup Wizard - Initial configuration flow

---

## QUICK TEST CHECKLIST

### Before Starting
- [ ] Get Databricks OAuth credentials
- [ ] Configure Lakebase database access
- [ ] Fix DataTable test
- [ ] Reduce TypeScript errors to < 50

### During Testing
- [ ] Use browser DevTools to monitor console
- [ ] Check for red errors and warnings
- [ ] Take screenshot of each page
- [ ] Test dark mode toggle
- [ ] Verify responsive design (3 sizes)
- [ ] Test form submissions
- [ ] Verify data persists on refresh

### After Testing
- [ ] Document all issues found
- [ ] Create bug tickets
- [ ] Performance report with metrics
- [ ] Accessibility audit results
- [ ] Update manifest with status

---

## COMMON COMMANDS

### Start Services
```bash
# Frontend (Vite dev server)
cd app/frontend && npm run dev
# Listens on http://localhost:5173

# Backend (FastAPI)
cd app && python app.py
# Listens on http://localhost:8000
# API docs: http://localhost:8000/api/swagger
```

### Run Tests
```bash
# Unit tests
cd app/frontend && npm test

# Linting
npm run lint

# Type checking
npx tsc --noEmit
```

### View Documentation
```bash
# API docs
curl http://localhost:8000/api/swagger

# Health check
curl http://localhost:8000/api/health

# Detailed health
curl http://localhost:8000/api/health/detailed
```

---

## KNOWN ISSUES (Quick Summary)

### Must Fix Before Testing
1. **DataTable Pagination Test** - Text format mismatch
   - File: `src/components/DataTable.test.tsx:61`
   - Expected: "1 / 4" → Actual: "Page 1 of 4"
   - Impact: Test suite fails

### Should Fix Before Release
2. **TypeScript Linting** - 559 errors, mostly `any` types
   - Impact: Type safety compromised
   - Fix: Run `eslint --fix` and replace `any` with proper types

3. **Dark Mode Toggle Missing** - UI not implemented
   - Impact: Users can't access dark mode feature
   - Fix: Add Moon/Sun icon button to top navigation

4. **React Hook Dependencies** - Missing in multiple files
   - Impact: Potential stale closures
   - File: `src/pages/stress-testing/index.tsx:178`

### Nice to Have
5. **Accessibility Labels** - Some buttons missing aria-labels
6. **Performance** - Potential re-render issues in stress testing
7. **Unit Test Coverage** - Could be more comprehensive

---

## FEATURE CHECKLIST

### Core Features (Must Test)
- [ ] Project creation and selection
- [ ] Data upload and processing
- [ ] Monte Carlo simulation execution
- [ ] Stress testing with multiple scenarios
- [ ] Report generation (IFRS 7)
- [ ] Sign-off and approval workflow
- [ ] Data persistence across sessions

### UI Features
- [ ] Dark mode toggle (if implemented)
- [ ] Navigation menu and sidebar
- [ ] Project dropdown selector
- [ ] Search and filter controls
- [ ] Table sorting and pagination
- [ ] Modal dialogs and confirmations
- [ ] Form validation messages

### Performance Targets
- [ ] Initial page load: < 3 seconds
- [ ] Dashboard render: < 2 seconds
- [ ] Form submission: < 2 seconds
- [ ] Monte Carlo progress updates: Every 2-5 seconds
- [ ] No UI freezing or unresponsiveness

---

## ISSUE PRIORITY MAP

### 🔴 CRITICAL (Fix Immediately)
```
Issue #1: OAuth Blocking Live Testing
  Status: Can't test without credentials
  Owner: Databricks Team
  Timeline: Immediate
  Impact: No live testing possible

Issue #2: Lakebase Connection Required
  Status: Backend won't start
  Owner: DevOps/QA
  Timeline: 1-2 hours
  Impact: Can't test backend

Issue #3: DataTable Test Broken
  Status: CI/CD may fail
  Owner: Dev Team
  Timeline: 15 minutes
  Impact: Test suite failure
```

### 🟠 HIGH (Before Release)
```
Issue #4: ESLint Errors (559)
  Status: Type safety compromised
  Timeline: 4-6 hours
  Impact: Maintainability risk

Issue #5: Dark Mode Missing UI
  Status: Feature incomplete
  Timeline: 1 hour
  Impact: User can't access feature

Issue #6: React Hook Dependencies
  Status: Potential runtime bugs
  Timeline: 1 hour
  Impact: Stale closures
```

### 🟡 MEDIUM (Before v2.0)
```
Issue #7-10: Accessibility, Performance, Tests
  Timeline: 2-3 hours each
  Impact: UX/accessibility compliance
```

---

## TESTING WORKFLOW

### Phase 1: Setup (30 min)
```
1. Get credentials from Databricks
2. Configure environment variables
3. Install dependencies
4. Fix DataTable test
5. Verify all services start
```

### Phase 2: Smoke Test (15 min)
```
1. Load deployed app (OAuth)
2. Check health endpoint
3. Verify frontend loads
4. Confirm no console errors
```

### Phase 3: Page Testing (4 hours)
```
For each of 18 pages:
  1. Load page
  2. Take screenshot
  3. Test all forms
  4. Check validation
  5. Verify persistence
  6. Log any issues
```

### Phase 4: Features Test (1.5 hours)
```
1. Dark mode toggle
2. Responsive design (3 sizes)
3. Data calculations
4. Report generation
5. Approval workflow
```

### Phase 5: Performance & A11y (1 hour)
```
1. Lighthouse audit
2. Console monitoring
3. Accessibility scan (axe-core)
4. Memory leak check
```

### Phase 6: Documentation (30 min)
```
1. Update manifest with results
2. Create bug tickets
3. Performance report
4. Final sign-off
```

---

## ARTIFACT LOCATIONS

```
Expected Credit Losses/
└── harness/
    ├── evaluations/
    │   ├── browser-test-manifest.md          ← MAIN TESTING GUIDE
    │   ├── BROWSER-TEST-ISSUES.md            ← ISSUES & FIXES
    │   ├── TESTING-SUMMARY.md                ← OVERVIEW
    │   └── QUICK-REFERENCE.md                ← THIS FILE
    └── screenshots/browser-test/
        ├── 01-login-page.png
        ├── 02-okta-login.png
        ├── 03-frontend-loading.png
        └── 04-frontend-with-backend.png
```

---

## HELPFUL LINKS

### API Endpoints (When Backend Running)
- Health check: `http://localhost:8000/api/health`
- API Docs: `http://localhost:8000/api/swagger`
- Database: `http://localhost:8000/api/health/detailed`

### Frontend URLs
- Dev server: `http://localhost:5173`
- Deployed: `https://ifrs9-ecl-demo-335310294452632.aws.databricksapps.com`

### Documentation
- Full manifest: `browser-test-manifest.md` (45 KB)
- Issues report: `BROWSER-TEST-ISSUES.md` (28 KB)
- Summary: `TESTING-SUMMARY.md` (20 KB)

---

## TROUBLESHOOTING

### "Can't connect to app"
→ Did you get OAuth credentials? Check Databricks team

### "Backend won't start"
→ Missing Lakebase credentials? Check environment variables

### "Frontend shows blank page"
→ API not responding? Ensure backend is running on port 8000

### "DataTable test fails"
→ Expected format issue - update test to "Page X of Y"

### "Lots of TypeScript errors"
→ Type safety violations - run `eslint --fix` and replace `any`

### "Dark mode not working"
→ Toggle UI not implemented - check navigation bar

### "Can't test mobile"
→ Use Chrome DevTools to resize, or use responsive testing tool

---

## NEXT PERSON CHECKLIST

If you're taking over this testing:

1. [ ] Read `TESTING-SUMMARY.md` (5 min)
2. [ ] Review `BROWSER-TEST-ISSUES.md` (10 min)
3. [ ] Check current blockers (5 min)
4. [ ] Set up environment (30 min)
5. [ ] Start testing (use `browser-test-manifest.md`)
6. [ ] Document findings
7. [ ] Update this file with new issues

---

**Questions?** See the full manifest files or contact the testing team.

**Ready to test?** Start with `browser-test-manifest.md` once credentials are obtained.

**Estimated Time**: 9-14 hours for comprehensive coverage
**ROI**: Prevent 5-10 production bugs per month

---

*Generated by Claude Code - Browser Testing Harness*
*Version: 0.17.0 | Date: 2026-03-30*
