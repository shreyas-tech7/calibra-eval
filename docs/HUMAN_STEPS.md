# Human steps

Steps that only Shreyas can do, in order. The build session had no working GitHub token and no
reachable model provider, so several usual steps moved here.

Release commit SHA: RELEASE_SHA_PLACEHOLDER

## 1. Create the GitHub repo and push the code

The build pushed to a local Git remote. A bundle of every branch is in the project files at
`portfolio/bundles/calibra-eval.bundle`.

1. On GitHub, create a new private repo named `calibra-eval` under `shreyas-tech7`. Add no README.
2. Download `calibra-eval.bundle`, then run:

   ```bash
   git clone calibra-eval.bundle calibra-eval
   cd calibra-eval
   git remote set-url origin https://github.com/shreyas-tech7/calibra-eval.git
   git push origin --all
   ```

## 2. Check that CI runs

Open the Actions tab of the repo. The `CI` workflow should run on the push of
`claude/build-calibra-eval` and finish green in under 5 minutes. The build session ran the same
steps locally (`./init.sh`, `calibra readme --check`, `scripts/replay_twice.sh`) and all passed.

## 3. Open and merge the pull request

1. Open a pull request from `claude/build-calibra-eval` into `main`.
2. Read the diff. The `Eval comment` workflow should post the results table on the pull request.
3. Merge with a merge commit (not squash), so the release commit stays in the history of `main`.

## 4. Tag the release candidate

```bash
git fetch origin
git tag -a v0.1.0-rc1 RELEASE_SHA_PLACEHOLDER -m "Release candidate 1"
git push origin v0.1.0-rc1
```

Or create a pre-release with that tag on GitHub.

## 5. Run the secret scan once more

```bash
gitleaks git -v .
```

The build ran it on the full history with no findings. `.gitleaks.toml` allows only the
SHA-256 fixture keys.

## 6. Record mode on a free provider

This is the step that turns simulated numbers into real ones (features F15 and F16).

1. Create a free key at a provider with an OpenAI-compatible endpoint, for example Groq
   (https://console.groq.com/keys) or OpenRouter (https://openrouter.ai/keys). Check the free
   limits first. Send only synthetic or public text, because some free tiers can train on prompts.
2. Pick a free judge model and put its id in `examples/judge_calibration/suite.real.toml`.
3. Run locally:

   ```bash
   ./init.sh
   export LLM_BASE_URL=https://api.groq.com/openai/v1
   export LLM_API_KEY=your-key            # never commit it
   .venv/bin/calibra run --record examples/judge_calibration/suite.real.toml
   ```

   That makes `results/judge_calibration_real.json` and
   `examples/judge_calibration/fixtures.real.jsonl` (216 calls). On HTTP 429, a server error or a
   dropped connection, the adapter waits and doubles the wait, up to 5 tries. If the run still
   stops, the calls recorded so far are saved, so the next run picks up where it stopped. If the provider keeps refusing, cut the judge cases to 30 and
   record over several sessions, then state the sample size.

4. Or run the `Record (manual)` workflow from the Actions tab after you add the secret
   `LLM_API_KEY` and the variable `LLM_BASE_URL` in the repo settings.
5. Run `calibra readme`, then `./init.sh`, commit the new fixtures and results, and push. The
   README picks up the real judge table on its own.
6. Set F15 and F16 to `"passes": true` in `feature_list.json` once their steps pass.

## 7. Make the repo public

All history becomes public at that moment. Decide first whether `docs/build/BUILD_PROMPT.md`
stays public. It is the full prompt that drove the build.

## 8. Fill in the About box and upload the social preview

The values and `gh api` commands are in `docs/GITHUB_ABOUT.md`. Upload `docs/social-preview.png`
under Settings, General, Social preview.

## 9. Pages

The results page `docs/index.html` opens from disk. To serve it, turn on Pages under Settings,
Pages, with source "Deploy from a branch", branch `main`, folder `/docs`.

## 10. Pin the repo

Pin it on your profile or list it in your profile README.

## 11. Publish to PyPI (optional)

The name `calibra-eval` was free on PyPI on 2026-11-20. Use trusted publishing: add a publisher
for `shreyas-tech7/calibra-eval` on PyPI, then add a release workflow. Check the name again first.

## 12. Human checks still open

The README lists these as "not done yet". Update it after you do them.

- Read the diff.
- Check the hand-computed values in `tests/reference/HAND_CALCULATIONS.md`.
- Look at the first real judge run.
