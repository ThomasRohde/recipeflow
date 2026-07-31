# M6 - Multi-recipe planning

## Deliverables

Recipe composition, reusable resource occupancy, duration-aware scheduling, target serving
time, critical path, parallel work, mise-en-place projection, and shopping-list projection.

## Boundary

Planning consumes canonical single-recipe graphs but remains a separate service and result
contract. It does not add meal-scheduling fields to the core authoring document.

## Evidence and exit

Fixtures combine several recipes under oven, burner, pan, and cook constraints. Results are
deterministic, explain unknown durations, and identify dependency/resource conflicts rather
than inventing a feasible schedule.
