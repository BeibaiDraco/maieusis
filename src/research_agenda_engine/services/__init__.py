"""Service layer.

This package intentionally re-exports NOTHING. Import services from
their submodules directly. The old eager re-export surface executed the legacy
R4 service layer (pipeline/contract/qbench/answerability/value/...) on any
``services.*`` import, dragging it into the product import closure
(``scripts/import_closure.py check`` guards that boundary).
"""
