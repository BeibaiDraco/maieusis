# 0.1.1 cleanroom release-validation profiles

These three strict profiles are the templates used to qualify a release: before Maieusis publishes a
version, the exact wheel it will publish must run all three datasets end to end from a clean
install, with no repair and no resume. They are reproduction inputs, not a starting point for your
own project — for that, use `examples/maieusis.yaml`.

Replace every `/ABSOLUTE/PATH/TO/...` value with a local path before preflight. Climate, IBL and NLB
each build a fresh PaperBank; none may import another run, and all three must run from one installed
wheel, in that order.

The files intentionally omit personal contact addresses. Operators may add a contact email to the
Crossref/OpenAlex fields when public-metadata access is authorized. Those operational values become
part of the final config-byte bindings but do not alter the frozen scientific profile.

These are qualification inputs, not demonstrations and not a publication authorization. Running them
costs real money, and passing them is one required step before a release is published, not the
release itself.
