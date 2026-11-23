"""Dependency-ordered planning that refuses a cycle.

Domain research: a plan whose phases depend on each other must be topologically
ordered, and a dependency cycle must be refused rather than partially executed.
The valuable part is reporting WHERE the cycle is, because a planner that says
"cannot order this" is useless and one that names the loop can be fixed. Partial
computation is also refused: no plan is emitted unless the whole graph orders.
"""
from collections import deque


class DynamicPhaseReplanner:
    def __init__(self):
        self._edges = {}   # phase -> set of phases it depends on
        self._names = []

    def phase(self, name, depends_on=()):
        if name not in self._edges:
            self._edges[name] = set()
            self._names.append(name)
        for d in depends_on:
            self._edges[name].add(d)
            if d not in self._edges:
                self._edges[d] = set()
                self._names.append(d)
        return name

    def order(self):
        """Topological order, or raise with the cycle named. Never partial."""
        indeg = {n: 0 for n in self._edges}
        for n, deps in self._edges.items():
            for d in deps:
                indeg[n] += 1
        # deterministic: declaration order as tie-break
        rank = {n: i for i, n in enumerate(self._names)}
        ready = deque(sorted([n for n in self._edges if indeg[n] == 0],
                             key=lambda n: rank[n]))
        out = []
        while ready:
            n = ready.popleft()
            out.append(n)
            for m in self._edges:
                if n in self._edges[m]:
                    indeg[m] -= 1
                    if indeg[m] == 0:
                        ready.append(m)
            ready = deque(sorted(ready, key=lambda x: rank[x]))
        if len(out) != len(self._edges):
            cyc = self.find_cycle()
            raise ValueError("dependency cycle: " + " -> ".join(cyc))
        return out

    def find_cycle(self):
        """Return one cycle, for an error message a human can act on."""
        colour = {n: 0 for n in self._edges}
        stack = []

        def visit(n):
            colour[n] = 1
            stack.append(n)
            for d in sorted(self._edges[n]):
                if colour.get(d, 0) == 1:
                    i = stack.index(d)
                    return stack[i:] + [d]
            for d in sorted(self._edges[n]):
                if colour.get(d, 0) == 0:
                    found = visit(d)
                    if found:
                        return found
            colour[n] = 2
            stack.pop()
            return None

        for n in sorted(self._edges):
            if colour[n] == 0:
                c = visit(n)
                if c:
                    return c
        return []
