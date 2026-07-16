"""Generic documentation-side narrator sources.

Two independent ``seed -> coarse facts`` feeds that share GF-2a's coarse-facts schema, distinguished
only by a provenance URI: Source A (deterministic documentation fetch) and Source C (frontier-model
self-research via web search). Plus the generic seed-link narrative source provider and the shared
coarse-facts import firewall. No A+B+C merge, no fidelity gate — those are GF-2c.
"""

from .coarse_facts_import import import_coarse_facts

__all__ = ["import_coarse_facts"]
