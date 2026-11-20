# Tooling

Tools set up for this build VM only. Nothing from a third-party skill is committed.

| Tool | Source | Version | Why | Check result |
| --- | --- | --- | --- | --- |
| gitleaks | go install github.com/zricethezav/gitleaks/v8 | v8.30.1 | secret scan before each commit | installed |
| actionlint | go install github.com/rhysd/actionlint | v1.7.12 | lint workflow files | installed |
| pip-audit | uv tool install pip-audit | 2.10.1 | dependency check | installed |
| pre-commit | uv tool install pre-commit | latest on 2026-11-20 | runs the gitleaks hook | installed |
| graphify | uv tool install graphifyy | latest on 2026-11-20 | resume runs on large code | installed, not needed yet |
| skill-scanner | uv tool install cisco-ai-skill-scanner | latest on 2026-11-20 | scan new skills | installed, no new skills to scan |
| ruff | preinstalled | 0.16.9 | lint and security rules | installed |
| superpowers skills | already present in the session | session copy | plans, TDD, debugging, verification, review | used |
| ponytail, caveman, find-skills, humanizer | npx skills add | none | style, token saving, docs pass | blocked: the session permission system refused `npx skills add`. Rules applied by hand |
