"""Change dependency types an inherited recipe declares.

Subclass directives cannot remove a type: ``depends_on`` merges types. The
class's queued ``depends_on`` directives are rewritten instead, before Spack
runs them on first use.
"""

from functools import partial

from spack.package import Spec


def restrict_dependency_type(cls, name, types):
    """Limit every ``depends_on(name)`` of ``cls`` to ``types``; drop the empty ones."""
    allowed = {types} if isinstance(types, str) else set(types)
    directives = cls._directives_to_be_executed["depends_on"]
    rewritten = []
    matched = False
    for directive in directives:
        spec = directive.keywords.get("spec")
        if isinstance(spec, str):
            spec = Spec(spec)
        if spec is None or spec.name != name:
            rewritten.append(directive)
            continue
        matched = True
        declared = directive.keywords["type"]
        declared = {declared} if isinstance(declared, str) else set(declared)
        kept = declared & allowed
        if kept:
            rewritten.append(partial(directive, type=tuple(sorted(kept))))
    if not matched:
        raise RuntimeError("{}: no depends_on({!r}) to restrict".format(cls.__name__, name))
    directives[:] = rewritten
