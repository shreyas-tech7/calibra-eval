# Blockers

What failed, the exact error, and what was done instead.

## B1. No free provider is reachable (open)
- 2026-11-20: `curl https://api.groq.com/openai/v1/models` and `curl https://openrouter.ai/api/v1/models` both fail with `curl: (56) CONNECT tunnel failed, response 403`. No `GROQ_API_KEY`, `OPENROUTER_API_KEY` or `LLM_API_KEY` variable exists.
- Instead: every run uses the deterministic fake model in `src/calibra_eval/fake.py`. F15 (record run on a free provider) and F16 (real judge model) stay `"passes": false`.
- Manual step: docs/HUMAN_STEPS.md, "Record mode on a free provider".

## B2. No GitHub access (open)
- 2026-11-20: the GitHub token in this session does not work and no GitHub repo is attached. `origin` is a local bare repo.
- Instead: CI steps run locally through `./init.sh` and `actionlint`. Repo settings, PR, tag and release steps are in docs/HUMAN_STEPS.md.

## B3. Skill installs refused (open)
- 2026-11-20: `npx -y skills add obra/superpowers ...` and the other skill installs were denied by the session permission system.
- Instead: used the superpowers skills that were already loaded. Ponytail, caveman and humanizer rules were applied by hand. Logged in docs/TOOLING.md.

## B4. huggingface.co, api.osv.dev and semgrep.dev blocked (open)
- 2026-11-20: each answers `CONNECT tunnel failed, response 403`.
- Instead: no embedding model is needed. pip-audit uses PyPI data. ruff `--select S` replaces semgrep.
