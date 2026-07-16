"""Planning services (dataset-planner handoff, artifact import, plan revision, guards).

This package intentionally re-exports NOTHING. Import planning
helpers from their submodules directly. The old eager re-export surface loaded
every planning module — including the retired shared_variability
scaffolding — on any ``services.planning.*`` import, dragging it into the
product import closure (``scripts/import_closure.py check`` guards that
boundary).
"""
