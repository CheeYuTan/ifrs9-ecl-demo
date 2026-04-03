# Sprint 3 Contract: User Guide — Workflow Steps 5-8

## Acceptance Criteria

- [ ] `step-5-model-execution.md` — ≥150 lines, covers Monte Carlo simulation for business users (no math/code), running a simulation, monitoring convergence, understanding results and confidence intervals
- [ ] `step-6-stress-testing.md` — ≥150 lines, covers all 5 analysis tabs (Monte Carlo Distribution, Sensitivity, Vintage, Concentration, Migration), interpretation guidance for each
- [ ] `step-7-overlays.md` — ≥150 lines, covers why overlays exist (IFRS 9 B5.5.17), adding overlays with rationale, governance framework (15% cap), impact on ECL, expiry/classification
- [ ] `step-8-sign-off.md` — ≥150 lines, covers 4-point attestation, hash verification, audit trail, attribution waterfall, segregation of duties, project immutability post-sign-off
- [ ] All pages follow established template: frontmatter → intro → prerequisites → What You'll Do → Step-by-Step → Understanding Results → Tips/Best Practices → What's Next
- [ ] Zero Python/JSON/API references in any page (strict User Guide persona isolation)
- [ ] All IFRS 9 terminology correct per spec terminology table
- [ ] `npm run build` succeeds with 0 errors
- [ ] Deployed to `docs_site/`

## Test Plan
- Build verification: `cd docs-site && npm run build` — 0 errors
- Line count: `wc -l` on each file ≥ 150
- Content audit: no code blocks, no API endpoints, no JSON, no Python in any of the 4 files
- Cross-reference: all internal links resolve (checked via build warnings)
- Deploy: `rm -rf ../docs_site/* && cp -r build/* ../docs_site/`

## Production Readiness Items This Sprint
- N/A (documentation-only sprint)
