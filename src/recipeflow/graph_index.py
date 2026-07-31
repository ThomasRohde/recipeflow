from __future__ import annotations

from collections import defaultdict, deque
from types import MappingProxyType

from recipeflow.exceptions import GraphInvariantError
from recipeflow.models.graph import (
    EdgeKind,
    MaterialNode,
    OperationNode,
    RecipeGraph,
)


class GraphIndex:
    """Immutable indexes and topology queries over a canonical recipe graph."""

    _frozen: bool

    def __init__(self, graph: RecipeGraph) -> None:
        self.graph = graph
        node_ids = [node.id for node in graph.nodes]
        if len(set(node_ids)) != len(node_ids):
            raise GraphInvariantError("Graph node IDs are not unique")
        self.materials = MappingProxyType(
            {
                node.id: node
                for node in graph.nodes
                if isinstance(node, MaterialNode)
            }
        )
        self.operations = MappingProxyType(
            {
                node.id: node
                for node in graph.nodes
                if isinstance(node, OperationNode)
            }
        )
        known_nodes = set(self.materials) | set(self.operations)
        invalid_edges = [
            edge.id
            for edge in graph.edges
            if edge.source not in known_nodes or edge.target not in known_nodes
        ]
        if invalid_edges:
            raise GraphInvariantError(
                f"Graph contains edges with missing endpoints: {invalid_edges}"
            )
        self.incoming = MappingProxyType(
            {
                node_id: tuple(
                    sorted(
                        (edge for edge in graph.edges if edge.target == node_id),
                        key=lambda edge: edge.id,
                    )
                )
                for node_id in known_nodes
            }
        )
        self.outgoing = MappingProxyType(
            {
                node_id: tuple(
                    sorted(
                        (edge for edge in graph.edges if edge.source == node_id),
                        key=lambda edge: edge.id,
                    )
                )
                for node_id in known_nodes
            }
        )
        object.__setattr__(self, "_frozen", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_frozen", False):
            raise AttributeError("GraphIndex is immutable")
        object.__setattr__(self, name, value)

    def material_inputs(self, operation_id: str) -> tuple[str, ...]:
        return tuple(
            sorted(
                edge.source
                for edge in self.incoming.get(operation_id, ())
                if edge.source in self.materials
                and edge.kind
                in {
                    EdgeKind.CONSUMES,
                    EdgeKind.RESERVES,
                    EdgeKind.OPTIONALLY_APPLIES,
                }
            )
        )

    def material_outputs(self, operation_id: str) -> tuple[str, ...]:
        return tuple(
            sorted(
                edge.target
                for edge in self.outgoing.get(operation_id, ())
                if edge.target in self.materials
                and edge.kind
                in {
                    EdgeKind.PRODUCES,
                    EdgeKind.RESERVES,
                    EdgeKind.DISCARDS,
                }
            )
        )

    def material_producer(self, material_id: str) -> str | None:
        producers = [
            edge.source
            for edge in self.incoming.get(material_id, ())
            if edge.source in self.operations
            and edge.kind
            in {
                EdgeKind.PRODUCES,
                EdgeKind.RESERVES,
                EdgeKind.DISCARDS,
            }
        ]
        return min(producers) if producers else None

    def material_consumers(self, material_id: str) -> tuple[str, ...]:
        return tuple(
            sorted(
                edge.target
                for edge in self.outgoing.get(material_id, ())
                if edge.target in self.operations
                and edge.kind
                in {
                    EdgeKind.CONSUMES,
                    EdgeKind.RESERVES,
                    EdgeKind.OPTIONALLY_APPLIES,
                }
            )
        )

    def operation_dependencies(self) -> dict[str, set[str]]:
        dependencies: dict[str, set[str]] = {
            operation_id: set()
            for operation_id in self.operations
        }
        for operation_id in self.operations:
            for material_id in self.material_inputs(operation_id):
                producer = self.material_producer(material_id)
                if producer:
                    dependencies[operation_id].add(producer)
            for edge in self.incoming.get(operation_id, ()):
                if (
                    edge.source in self.operations
                    and edge.kind in {EdgeKind.REQUIRES, EdgeKind.PRECEDES}
                ):
                    dependencies[operation_id].add(edge.source)
        return dependencies

    def topological_operation_ids(self) -> tuple[str, ...]:
        dependencies = self.operation_dependencies()
        successors: dict[str, set[str]] = defaultdict(set)
        indegree = {
            operation_id: len(required)
            for operation_id, required in dependencies.items()
        }
        for operation_id, required in dependencies.items():
            for prerequisite in required:
                successors[prerequisite].add(operation_id)
        queue = deque(
            sorted(
                operation_id
                for operation_id, degree in indegree.items()
                if degree == 0
            )
        )
        result: list[str] = []
        while queue:
            operation_id = queue.popleft()
            result.append(operation_id)
            for successor in sorted(successors[operation_id]):
                indegree[successor] -= 1
                if indegree[successor] == 0:
                    queue.append(successor)
        if len(result) != len(self.operations):
            raise GraphInvariantError("Graph operation dependencies contain a cycle")
        return tuple(result)

    def parallel_operation_groups(self) -> tuple[tuple[str, ...], ...]:
        dependencies = self.operation_dependencies()
        remaining = set(dependencies)
        completed: set[str] = set()
        groups: list[tuple[str, ...]] = []
        while remaining:
            ready = tuple(
                sorted(
                    operation_id
                    for operation_id in remaining
                    if dependencies[operation_id] <= completed
                )
            )
            if not ready:
                raise GraphInvariantError("Graph operation dependencies contain a cycle")
            groups.append(ready)
            completed.update(ready)
            remaining.difference_update(ready)
        return tuple(groups)

    def connected_components(self) -> tuple[tuple[str, ...], ...]:
        all_nodes = set(self.materials) | set(self.operations)
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in self.graph.edges:
            adjacency[edge.source].add(edge.target)
            adjacency[edge.target].add(edge.source)
        components: list[tuple[str, ...]] = []
        remaining = set(all_nodes)
        while remaining:
            start = min(remaining)
            queue = [start]
            component: set[str] = set()
            while queue:
                node = queue.pop()
                if node in component:
                    continue
                component.add(node)
                queue.extend(sorted(adjacency[node] - component, reverse=True))
            remaining -= component
            components.append(tuple(sorted(component)))
        return tuple(sorted(components))
