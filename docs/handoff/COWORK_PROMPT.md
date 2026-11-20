# Prompt for Claude Cowork

Paste everything below the line into Claude Cowork.

---

You are helping Shreyas finish the browser steps for his private GitHub repo
`shreyas-tech7/calibra-eval`. Do not ask questions. Do not stop without a result. Use plain
words in your report.

Context: an unattended Claude Code session built the repo. It had no GitHub access, so Shreyas
first creates the repo and pushes the code himself (docs/HUMAN_STEPS.md step 1). Start only after
the repo exists on GitHub. If it does not exist yet, stop and say so.

Do these steps. Each is free and can be undone.

1. Open the Actions tab. Report whether the `CI` workflow ran on branch
   `claude/build-calibra-eval` and whether it passed. If it failed, copy the name of the failed
   step and the last 20 lines of its log into your report.
2. Open the pull request from `claude/build-calibra-eval` into `main`, if Shreyas opened one.
   Report whether the `Eval comment` workflow posted a results table. Do not merge it.
3. Open Settings, General. Fill in the About box with the description and topics from
   `docs/GITHUB_ABOUT.md` in the repo. Upload `docs/social-preview.png` as the social preview.
4. Report what you changed and what you saw.

Do not do any of these:

- Do not make the repo public.
- Do not merge, tag or delete anything.
- Do not publish a package.
- Do not create or enter any key, token or secret.
- Do not sign in to any site for Shreyas.
- Do not pay for anything or start a trial.

Finish with the next prompt for Claude Code, in a code block, with:

- Context: the repo, branch `claude/build-calibra-eval`, and what you saw in steps 1 to 3.
- What is complete: every feature in `feature_list.json` except F15 and F16 (record mode).
- What is open: record mode on a free provider (docs/HUMAN_STEPS.md step 6), any CI failure you
  found, the human checks in step 12.
- This resume launcher, word for word: "Read docs/build/BUILD_PROMPT.md and follow it. Resume
  from PROGRESS.md on branch claude/build-calibra-eval. Do not ask questions. Do not stop until
  every Done-means item is true or blocked with a fallback."
