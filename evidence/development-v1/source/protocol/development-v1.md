# Development v1 — frozen before model execution

Question: does context-dependent supervised experience improve complete service
allocation, and does the gain persist through two current-policy corrections?
EU1–EU3 remain unchanged in README. This controlled experiment is not a natural
service deployment or a replication of cited papers.

Each request has entity, plan binding, requested units, available units, urgent
flag and waiver flag. The authoritative current policy supplies plan caps, urgent
cap replacement, per-unit fee, urgent surcharge and shipping lane. All methods
receive the same schema, authority and full evidence, without retrieval error.
Output is units, total fee, lane and leftover stock. Units are bounded by request,
stock and the applicable cap. Zero units means fee zero and lane NONE. Waivers
remove surcharge only. Complete correctness requires all four fields; format and
per-field correctness are secondary. No teacher reasoning is acquired.

Two equal-update histories: stable repeats a 64-case bank with fixed policy;
varied changes cap/price/lane bindings across four policy worlds for the same
requests, so old answers do not suffice. Both see all rules. Difference includes
policy diversity, not an isolated causal manipulation of memorization. 8 familiar
entities; held-out queries and 8 fresh entity bindings assess use separately.
Shared pretrained start, same adapter initialization, rank8 last8 q/v LoRA,
CE AdamW 5e-4, checkpoints128/256 updates per arm. No selection by correction
performance. Both checkpoints assessed and all failed outputs retained.

Controls: base with current evidence; base with investigator-written procedural
lesson and four worked examples selected from each history (varied and stable
lesson variants); executable interpreter with supplied schema/operations. Lessons
contain no information absent from rules/training records, but human derivation
is supplied effort. Examples retain their own labeled historical policies.

Evaluation: 32 cases per policy version, half familiar entities and half fresh.
Version1 replaces plan A's urgent cap and lane. Version2 changes plan B's price
and ordinary cap while retaining revision1. Report newly changed and unchanged
complete answers and paired retention, not only aggregate accuracy. Development
seed731; fresh assessment seed947 is reserved until recipe freezes. Fresh cases
have disjoint entity identifiers and numerical requests. Final will train a new
state, so inference is not solely conditional on a chosen development adapter.

Finite budget: development <=512 total updates, <=1000 model generations,
30 minutes wall per invocation including waits,32GiB MLX peak allocation checked
between operations; Metal allocation limit32GiB, cache2GiB. These are not a total
RSS guarantee. No concurrent heavy local Python model job permitted at launch;
record process inventory and acquire own file lock. Abort if a new competing
study model job is seen. No hardware purchase or paid model API. Fresh run has
same cap. At most one bounded diagnostic of <=256 extra updates if acquisition
fails; its design must be documented before execution. Useful acquisition means
improved complete fresh-case outcomes, not loss or gradients. Save gradients,
adapter change and base/reset invariants, then reload probes in a fresh process.

Record inputs, outputs, tokens, seconds, updates, source snapshots, model hashes,
checkpoint bytes and correction bytes. Timings are observed local costs, not an
isolated hardware benchmark. Experimental search, verification and deployed
trajectory costs remain separate. No hypothetical-use repayment claim.
