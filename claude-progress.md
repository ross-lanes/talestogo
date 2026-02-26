# Project Progress

## Last Session: 2026-02-26

### Completed
- Fixed all Checkmarx SAST true positive findings (~35 issues)
- Deleted 23 root-level one-off scripts with hardcoded DB credentials
- Deleted 2 data export scripts with SQL injection vulnerabilities
- Replaced hardcoded DB URLs with env vars in 6 scripts under scripts/
- Sanitized 5 documentation files (replaced real credentials with placeholders)
- Added HSTS header to SecurityHeadersMiddleware in app/main.py
- Replaced hardcoded temp password in user invitation with secrets-based random generation
- Updated .gitignore to prevent future credential leaks
- Verified zero credential strings remain in tracked codebase
- Ran app locally, confirmed HSTS header present in responses
- Wrote SAST remediation summary Word doc for PNNL (SAST_Remediation_Summary_PNNL.docx, local only)
- Updated deployment-kit IT guide with HSTS header, regenerated Word docs
- Pushed all changes to both GitHub and PPPL GitLab

### Current State
- **App Status:** Working (verified locally)
- **Known Issues:** None from SAST remediation
- **Commits:**
  - `ac4eeb50` - Remove hardcoded credentials and fix SAST findings (38 files, +72/-2145)
  - `aa54b1b8` - Update deployment kit with HSTS header and regenerate Word docs

### Blockers
- None

---

## Next Session Focus
- Await PNNL rescan results; address any remaining findings if needed
- False positives documented in SAST_Remediation_Summary_PNNL.docx for their reference
