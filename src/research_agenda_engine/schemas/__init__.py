"""Typed scientific artifact schemas.

This package intentionally re-exports NOTHING. Import schemas from
their submodules directly (e.g. ``from research_agenda_engine.schemas.research_intent
import ResearchIntent``). The old eager re-export surface executed every schema
module — including legacy question/ideation/r4 — on any schema import, dragging
the whole legacy layer into the product import closure
(``scripts/import_closure.py check`` guards that boundary).
"""
