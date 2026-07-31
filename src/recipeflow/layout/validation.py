from recipeflow.models.common import Diagnostic, Severity
from recipeflow.models.layout import Rect, TabularLayout


def validate_tabular_layout(layout: TabularLayout) -> tuple[Diagnostic, ...]:
    diagnostics: list[Diagnostic] = []
    canvas = Rect(x=0, y=0, width=layout.width, height=layout.height)

    identifiers = [
        *(block.id for block in layout.text_blocks),
        *(box.id for box in layout.boxes),
        *(path.id for path in layout.paths),
    ]
    duplicates = sorted(
        identifier for identifier in set(identifiers) if identifiers.count(identifier) > 1
    )
    for identifier in duplicates:
        diagnostics.append(
            _diagnostic(
                "RF500",
                f"Layout element id '{identifier}' is not unique.",
                identifier,
            )
        )

    for block in layout.text_blocks:
        if block.overflow:
            diagnostics.append(
                _diagnostic(
                    "RF501",
                    f"Text block '{block.id}' reports overflow.",
                    block.id,
                )
            )
        if not canvas.contains(block.rect):
            diagnostics.append(
                _diagnostic(
                    "RF502",
                    f"Text block '{block.id}' lies outside the canvas.",
                    block.id,
                )
            )

    for box in layout.boxes:
        if not canvas.contains(box.rect):
            diagnostics.append(
                _diagnostic(
                    "RF503",
                    f"Content box '{box.id}' lies outside the canvas.",
                    box.id,
                )
            )

    for path in layout.paths:
        radius = path.stroke_width / 2
        if any(
            point.x - radius < 0
            or point.y - radius < 0
            or point.x + radius > layout.width
            or point.y + radius > layout.height
            for point in path.points
        ):
            diagnostics.append(
                _diagnostic(
                    "RF504",
                    f"Path '{path.id}' lies outside the canvas.",
                    path.id,
                )
            )

    opaque_boxes = [box for box in layout.boxes if box.opaque]
    for index, first in enumerate(opaque_boxes):
        for second in opaque_boxes[index + 1 :]:
            if first.rect.intersects(second.rect):
                diagnostics.append(
                    Diagnostic(
                        code="RF505",
                        severity=Severity.ERROR,
                        path=f"/boxes/{first.id}",
                        related_paths=(f"/boxes/{second.id}",),
                        message=(
                            f"Opaque content boxes '{first.id}' and "
                            f"'{second.id}' overlap."
                        ),
                        suggestions=(
                            "Increase row height or column width and reflow the layout.",
                        ),
                    )
                )
    return tuple(diagnostics)


def _diagnostic(code: str, message: str, identifier: str) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        path=f"/layout/{identifier}",
        message=message,
    )
