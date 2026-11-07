# OnAIR #207 follow-up — November 7, 2026

Incremental corrections on [PR #207](https://github.com/nasa/OnAIR/pull/207), preserving its author's per-channel missing-data policy.

- [Unequal-history correction](https://github.com/cstolting-collab/OnAIR/commit/9f6f4877118df3e48bb80f0649595ea5c3feda12): evaluate each ready channel and retain its header position.
- [Overflow and warning handling](https://github.com/cstolting-collab/OnAIR/commit/f859ec45a2bb65e937d6592ae4a0860fea119189): treat overflowing values as missing without crashing the warning path; preserve neighboring valid readings.
- [Test dependency](https://github.com/cstolting-collab/OnAIR/commit/ac160a6f1acfeb8269430471e17d89baabf72cae): declare Hypothesis, already used by the PR.
- [Formatting](https://github.com/cstolting-collab/OnAIR/commit/5e2230de7e8a1d266f0381969edbb8d33e04b312): separate formatting-only changes; syntax trees verified unchanged.

## Evidence

[Download the review package](OnAIR_207_Rework_2026-11-07.zip?raw=true) — patches, reproduction commands, logs, source hashes, and optional CML replay.

| Check | Original PR207 with the added tests | Reworked |
| --- | --- | --- |
| Full suite, identical 427 test identities | 405 pass / 22 fail | 427 pass / 0 fail |
| Real-library history lengths | 132 pass / 1422 fail | 1554 pass / 0 fail |
| Real-library stream updates | 281 pass / 719 fail | 1000 pass / 0 fail |
| Parser boundary cases | 24 pass / 232 fail | 256 pass / 0 fail |
| Repository Black check | 5 files require formatting | all 81 files pass |

Python 3.12.14, NumPy 2.5.4, simdkalman 1.0.4. No skips. A fresh installation from the original declared requirements failed collection in two modules because Hypothesis was absent. The reworked requirements allowed the full suite to run. Pylint retains advisory diagnostics under the repository's existing exit-zero setting; it is not warning-free. The hosted Python version matrix was not executed locally.

CML's unchanged StateGovernance runtime accepted all 2,810 reworked observations and rejected 11 negative controls. It enforces predicates computed by the Python observer; it does not independently validate telemetry physics. CML is optional review tooling, not an OnAIR dependency. CML source is not included.

## Scope and attribution

PR207's ingestion changes are **mrizvi96's work**. This series extends that work. [PR205](https://github.com/nasa/OnAIR/pull/205)'s numerical correction remains separate. Warm-up behavior, freshness, missing-sample time alignment, and prediction overflow from extreme finite inputs remain unresolved. No live telemetry, hardware validation, or NASA acceptance is represented.

Prepared with AI assistance and offered for review. This publication does not assert that NASA's requested human review or CLA process has been completed.

## Integrity and publication

Tested Git tree: `3a54d27c31c8571361e19409c919b01aab200b9a`.
Public code head: [`5e2230de7e8a1d266f0381969edbb8d33e04b312`](https://github.com/cstolting-collab/OnAIR/commit/5e2230de7e8a1d266f0381969edbb8d33e04b312).
The public commit trees exactly match the local tested trees; GitHub commit IDs differ because commit metadata differs.

ZIP SHA-256: `477a9ced719b8df590e19515a408d646299f2b1a718d3b3fa3c4f08439ffee62`.
ZIP Git blob: `ed9c2d8cd0f63956447ea46b7e7b8a8c9a9d6fe6`.

The archive is preserved unchanged from preparation. Its “not posted” statements describe that earlier snapshot. This index records publication of the code and evidence; the upstream PR remains the original author's PR.
