# 0.1.1 cleanroom release-validation profiles

These four strict profiles are the templates used to qualify a release: before Maieusis publishes a
version, the exact wheel it will publish must run every one of them end to end from a clean install,
shepherded, with no repair that touches the bytes being qualified. Maieusis is
agent-operated, so a qualifying run is driven the way any real run is — by a coding-agent session
under the shepherd-mode contract. What that session may not do is change the candidate, carry a run
past a scientific verdict, or repair past a guard. They are reproduction inputs, not a starting
point for your own project — for that, use `examples/maieusis.yaml`.

Replace every `/ABSOLUTE/PATH/TO/...` value with a local path before preflight. All four run from
one installed wheel. Climate and IBL each build a fresh PaperBank; the open-mode IBL run and NLB
import IBL's, which is recorded on the set receipt, so IBL must run before them. A leg that imports
inherits the bank's digest — it does not inherit the questions, which are proposed again from that
leg's own dataset context and research intent.

The files intentionally omit personal contact addresses. Operators may add a contact email to the
Crossref/OpenAlex fields when public-metadata access is authorized. Those operational values become
part of the final config-byte bindings but do not alter the frozen scientific profile.

These are qualification inputs, not demonstrations and not a publication authorization. Running them
costs real money, and passing them is one required step before a release is published, not the
release itself.
