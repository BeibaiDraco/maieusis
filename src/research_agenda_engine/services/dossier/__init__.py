"""Dossier services (generic dossier pipeline, multi-family orchestration, translation).

This package intentionally re-exports NOTHING. Import dossier
helpers from their submodules directly. The old eager re-export surface loaded
the retired legacy scientific_dossier module (and its shared_variability
chain) on any ``services.dossier.*`` import, dragging it into the product
import closure (``scripts/import_closure.py check`` guards that boundary).
"""
