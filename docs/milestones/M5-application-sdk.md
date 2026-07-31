# M5 - Application SDK

## Deliverables

Stable application services, incremental validation, source maps, portable result envelopes,
direct layout access, reviewed TypeScript declarations, and integration examples.

## Evidence

The examples under [examples/sdk](../../examples/sdk) run in CI. They use text or in-memory
models, serialize public results, and import no CLI module. Contract tests round-trip every
portable result through JSON Schema.

## Exit

A service or editor can consume every core capability without filesystem access or private
module imports.
