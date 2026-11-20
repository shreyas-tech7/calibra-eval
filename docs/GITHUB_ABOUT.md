# GitHub About box

Set these on the repo page (gear icon next to About), or with `gh api` once the repo exists.

**Description:** Offline agent evals that measure how far their own LLM judge can be trusted: kappa, bias probes, paired stats, full replay.

**Topics:** `llm-evaluation`, `evals`, `llm-as-a-judge`, `cohens-kappa`, `bootstrap`, `statistics`, `python`, `ai-agents`, `reproducibility`, `pass-at-k`

**Social preview:** upload `docs/social-preview.png` (1280 x 640) under Settings, General, Social preview.

```bash
gh api -X PATCH repos/shreyas-tech7/calibra-eval -f description="Offline agent evals that measure how far their own LLM judge can be trusted: kappa, bias probes, paired stats, full replay."
gh api -X PUT repos/shreyas-tech7/calibra-eval/topics -f "names[]=llm-evaluation" -f "names[]=evals" -f "names[]=llm-as-a-judge" -f "names[]=cohens-kappa" -f "names[]=bootstrap" -f "names[]=statistics" -f "names[]=python" -f "names[]=ai-agents" -f "names[]=reproducibility" -f "names[]=pass-at-k"
```
