# Inspected methods and provenance, 16 September 2026

Primary full texts inspected: Context-faithful Prompting2303.11315v2 §§3–4;
Context-Parametric Inversion2410.10796v3 §§3–4; CARE2509.13683v1 §§3–5.
Exact-version HTML and API metadata acquisition are recorded in sources/papers.
The API request is one cached ID-list query, followed by serial full texts spaced
at least3 seconds with descriptive User-Agent. No broad novelty claim is made.

Context-faithful prompting uses explicit context attribution and counterfactual
examples. Author code knowledge_conflict.py at7e2cfc2505ab00c1c06b7adef60eeda63b1cc5df
was inspected (qa_to_prompt and demonstration selection), copied for inspection,
not executed. Its old API and substring answer scoring are not used here.
Inversion distinguishes context-critical from redundant context; this motivates
varied versus stable policy histories, without reproducing its IFT experiment.
CARE combines supervised evidence reasoning with RL; its author-reported gains
already establish generic counterfactual reading feasibility. We do not adapt
its retrieval/RL implementation or claim reproduction. Our narrow residual is
complete service obligations, repeated authorized correction, and native costs.
No author-reported score is treated as local evidence.

Local implementation inspected: procedure-retention-and-revision at
3e71eb5f146e6493c60cef26d15d86dedd2249fb, its AGENTS, README and reproduction notes.
Copied runtime.py and model-reference.json; no sibling changed or inherited
learned adapter used. Runtime source retains its historical provenance field.
MLX-LM86b48c461feebf87c58788655b7e57b5574b9e6d tuner/utils.py and lora.py inspected:
last-block selection, q/v keys, direct scale convention, zero-B initialization.
Actual local model hashes and gradients/restoration still require run evidence.
Root-linked sources/2026-09-16-evidence-use ledger is absent in this checkout;
we rely on exact primary versions and the README overlap notes instead.
