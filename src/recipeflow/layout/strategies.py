from __future__ import annotations

import re
from threading import RLock
from typing import Protocol

from recipeflow.exceptions import (
    LayoutStrategyRegistrationError,
    UnknownLayoutStrategyError,
)
from recipeflow.layout.engine import create_flow_layout
from recipeflow.layout.options import LayoutOptions
from recipeflow.models.graph import RecipeGraph
from recipeflow.models.layout import TabularLayout
from recipeflow.typography import TextMeasurer


class LayoutStrategy(Protocol):
    """Deterministic graph-to-layout strategy used by tabular renderers."""

    def create_layout(
        self,
        graph: RecipeGraph,
        options: LayoutOptions,
        *,
        text_measurer: TextMeasurer | None = None,
    ) -> TabularLayout: ...


class FlowLayoutStrategy:
    def create_layout(
        self,
        graph: RecipeGraph,
        options: LayoutOptions,
        *,
        text_measurer: TextMeasurer | None = None,
    ) -> TabularLayout:
        return create_flow_layout(
            graph,
            options,
            text_measurer=text_measurer,
        )


_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[-.:][a-z0-9]+)*$")
_BUILTIN_NAMES = frozenset({"flow", "compact-table", "ledger"})
_LOCK = RLock()
_STRATEGIES: dict[str, LayoutStrategy] = {"flow": FlowLayoutStrategy()}


def _ensure_builtins() -> None:
    if "compact-table" in _STRATEGIES and "ledger" in _STRATEGIES:
        return
    from recipeflow.layout.compact_table import CompactTableLayoutStrategy
    from recipeflow.layout.ledger import LedgerLayoutStrategy

    _STRATEGIES.setdefault("compact-table", CompactTableLayoutStrategy())
    _STRATEGIES.setdefault("ledger", LedgerLayoutStrategy())


def register_layout_strategy(name: str, strategy: LayoutStrategy) -> None:
    """Register an explicitly imported third-party notation strategy.

    Third-party names are namespaced with ``vendor:name`` or ``vendor.name``.
    Built-ins and existing registrations cannot be replaced.
    """

    if not _NAME_PATTERN.fullmatch(name):
        raise LayoutStrategyRegistrationError(
            "Layout strategy names must use lowercase letters, digits, hyphens, "
            "dots, or colons."
        )
    if name not in _BUILTIN_NAMES and ":" not in name and "." not in name:
        raise LayoutStrategyRegistrationError(
            "Third-party layout strategy names must be namespaced, for example "
            "'acme:timeline'."
        )
    if not callable(getattr(strategy, "create_layout", None)):
        raise LayoutStrategyRegistrationError(
            "A layout strategy must implement create_layout()."
        )
    with _LOCK:
        _ensure_builtins()
        if name in _STRATEGIES:
            raise LayoutStrategyRegistrationError(
                f"Layout strategy '{name}' is already registered."
            )
        _STRATEGIES[name] = strategy


def get_layout_strategy(name: str) -> LayoutStrategy:
    with _LOCK:
        _ensure_builtins()
        try:
            return _STRATEGIES[name]
        except KeyError as exc:
            raise UnknownLayoutStrategyError(
                name,
                tuple(sorted(_STRATEGIES)),
            ) from exc


def list_layout_strategies() -> tuple[str, ...]:
    with _LOCK:
        _ensure_builtins()
        return tuple(sorted(_STRATEGIES))


def create_tabular_layout(
    graph: RecipeGraph,
    options: LayoutOptions | None = None,
    *,
    text_measurer: TextMeasurer | None = None,
) -> TabularLayout:
    """Create a renderer-neutral layout using the selected notation strategy."""

    selected = options or LayoutOptions()
    strategy = get_layout_strategy(selected.notation)
    layout = strategy.create_layout(
        graph,
        selected,
        text_measurer=text_measurer,
    )
    if layout.notation != selected.notation:
        raise LayoutStrategyRegistrationError(
            f"Layout strategy '{selected.notation}' returned notation "
            f"'{layout.notation}'."
        )
    return layout
