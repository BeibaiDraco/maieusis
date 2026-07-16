"""Retrieval services (topic sources, paper-case index, direct-recap, literature priors).

This package intentionally re-exports NOTHING. Import retrieval
helpers from their submodules directly. The old eager re-export surface loaded
every retrieval module — including the legacy ``direct_recap_expert_review``
surface — on any ``services.retrieval.*`` import.
"""
