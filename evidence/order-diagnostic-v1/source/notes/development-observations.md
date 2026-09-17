# Development observations

Before training outcomes: baseline55/96 complete, stable-history lesson68/96,
varied-history lesson67/96. All288 generations valid JSON, no output-limit hits.
Thus any subsequently observed complete improvement is not merely removing format
errors. Workload audit shows56/64 varied-history cases change answer across
training worlds (the8 zero-allocation cases remain invariant), zero exact request
overlap with evaluation, and12 changed/20 unchanged cases per correction.

The experiment follows a fixed schedule rather than selecting a checkpoint for
its correction score. Later fresh evaluation will use disjoint seed947 entity
identifiers and newly sampled requests on the same support. The development
protocol phrase “disjoint ... numerical requests” means disjoint complete case
identities, NOT unseen integer magnitudes: integer supports intentionally overlap.
This clarification prevents overstating extrapolation. The final assessment is
within the same controlled generator, not external natural-language transfer.
