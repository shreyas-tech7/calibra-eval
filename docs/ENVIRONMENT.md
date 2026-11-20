# Environment

Probed on 2026-11-20 from the build VM (Intel Xeon @ 2.10GHz, 4 cores, 15 GB RAM, Python 3.13.18, uv 0.11.32).

| Host | Result |
| --- | --- |
| https://api.groq.com/openai/v1/models | blocked: CONNECT tunnel failed, response 403 |
| https://openrouter.ai/api/v1/models | blocked: CONNECT tunnel failed, response 403 |
| https://huggingface.co | blocked: CONNECT tunnel failed, response 403 |
| https://api.osv.dev | blocked: CONNECT tunnel failed, response 403 |
| https://semgrep.dev | blocked: CONNECT tunnel failed, response 403 |
| https://pypi.org/pypi/calibra-eval/json | 404 (name free) |
| https://pypi.org/pypi/calibra_eval/json | 404 (name free) |
| https://pypi.org/pypi/judgelab/json | 404 (name free) |
| https://registry.npmjs.org/calibra-eval | 404 (name free) |
| https://registry.npmjs.org/judgelab | 404 (name free) |
| https://raw.githubusercontent.com | 301 (reachable) |
| https://github.com | 400 (reachable through the proxy) |

Provider keys: none of `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `LLM_API_KEY` is set.
