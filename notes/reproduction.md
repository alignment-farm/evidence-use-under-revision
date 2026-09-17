# Reproduction

Use Apple Silicon with64GiB memory and uv. The checked-in uv.lock pins MLX0.32.2
and MLX-LM86b48c461feebf87c58788655b7e57b5574b9e6d. Install with:

```sh
uv sync --python 3.14.7 --extra adaptation --frozen
```

Place Qwen/Qwen3-4B-Instruct-2507 revision
cdbee75f17c01a7cc42f958dc650907174af0554 under models/qwen3-4b-instruct.
The local run uses a read-only-input symlink to existing sibling weights; no
sibling files are changed. Model hashes are checked before loading using
sources/model-reference.json. We do not use a serving endpoint for gradients.

```sh
uv run --extra adaptation --no-sync python scripts/workload.py
uv run --extra adaptation --no-sync python scripts/experiment.py --output evidence/NEW-DEV --seed 731
uv run --extra adaptation --no-sync python scripts/analyze.py evidence/NEW-DEV --output evidence/NEW-DEV-analysis
uv run --extra adaptation --no-sync python scripts/audit.py evidence/NEW-DEV --output evidence/NEW-DEV-audit
```

Never reuse an output directory; failed attempts must remain. All run sources,
protocols, model hash records, history, current policies, generated text/token IDs,
update counts and checkpoint hashes are saved. Analysis checks all artifact hashes,
re-scores complete answers through a separately written textual interpreter, and
reports changed/unchanged cases plus paired retention. Reload audits verify token
accounting and sample each saved endpoint across fresh/familiar, corrected and
uncorrected, successful and failed cases, with exact output agreement. These
verification calls are not additional accuracy samples.

The initial launcher failure at evidence/development-v1 contains no model work.
The corrected development-v2 starts at aba9622. Later analysis code is independently
versioned; no completed raw event is edited. Training and generation timers exclude
hashing, orchestration and verification; status wall time includes runtime setup.
MLX peak allocation is not full system memory. Process guards do not establish
isolated timing or coordinate unrelated non-Python workloads.

## Diagnostic and frozen fresh assessment

The equal-data ordering diagnostic was launched at8a38945 and published atcc935da;
its audit and data/control identity check are at8e93219. Final execution starts
at8e93219 with the conditional recipe decision already fixed:

```sh
uv run --extra adaptation --no-sync python scripts/experiment.py --output evidence/NEW-ORDER --seed 731 --arms varied --shuffle
uv run --extra adaptation --no-sync python scripts/experiment.py --output evidence/NEW-FRESH --seed 947 --shuffle --rebind
uv run --extra adaptation --no-sync python scripts/analyze.py evidence/NEW-FRESH --output evidence/NEW-FRESH-analysis
uv run --extra adaptation --no-sync python scripts/audit.py evidence/NEW-FRESH --output evidence/NEW-FRESH-audit
```

Run heavy commands sequentially. The independent fresh bindings are deliberate;
see protocol/final-v1.md. Identical integer supports do not imply identical
requests or entity bindings. The earlier development analysis failure selected
a historical request from a lesson prompt; notes/analysis-repair.md explains its
repair and regression checks. Original raw scores did not change.

`scripts/publish.py --output evidence/NEW-PUBLICATION` rebuilds the final ledger
from the three named audited runs; for a full rerun, change its `specs` paths to
your newly generated directories. Counts include failed-quality endpoints and
training-fit probes. It distinguishes candidate96-use trajectories from total
investigation costs. The launch failure and empty failed analysis remain recorded.
Model generations use new prompt caches; no method receives persistent KV prefix
reuse. Times therefore describe this implementation, not an optimal serving stack.
Investigator lesson/algorithm construction effort is disclosed but not timed or
priced. Adapter loading, source hashing and audits are not silently counted as
zero; they are included in run wall/audit costs rather than per-use model timers.
