# GitHub Pages Direct Deploy Spec

## Goal

Make one push to `main` sufficient to build, verify, package, and publish the Marvel flowchart, so manual follow-up pushes are unnecessary.

## Requirements

- `main` pushes build `index.html` from the versioned source under `src/` and `scripts/`.
- The existing release-contract tests continue to run before deployment.
- Pull requests targeting `main` run build and verification but never deploy.
- The deployed site contains exactly the six public files: `index.html`, `README.md`, `AUDIT.md`, `AUDIT.json`, `preview.png`, `.nojekyll`.
- GitHub Pages is deployed directly with `actions/upload-pages-artifact` and `actions/deploy-pages`.
- The workflow must not create or push a bot commit. Publication must not depend on a second workflow trigger.
- A downloadable Actions artifact with the same six public files is produced for each successful `main` run.
- `workflow_dispatch` is available for a manual re-run without changing repository contents.
- The workflow uses read-only repository contents permission; only Pages and OIDC deployment permissions may be writable.

## Acceptance

A pull-request run must pass all source/release tests and the workflow contract test. After merge, the `main` workflow must reach the Pages deployment job from the same run. If GitHub repository settings still use branch-based Pages publishing, the only remaining manual action is the one-time switch of Pages Source to GitHub Actions.
