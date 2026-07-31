# Security policy

## Trust boundary

Recipe documents and external recipe content are untrusted data. RecipeFlow parses them as
data and never executes embedded instructions, templates, scripts, URLs, or markup.

Core services perform no network access, browser automation, model calls, subprocess
invocation, or credential discovery. Acquisition tools remain outside the package.

## Parser and renderer rules

- Use safe YAML loading; reject language-specific object tags.
- Bound input size, collection depth, graph size, and rendered dimensions at adapter
  boundaries where denial of service matters.
- Escape all authored text in SVG, HTML, Mermaid, and diagnostic presentation.
- Never interpolate authored identifiers into filesystem paths.
- Do not dereference source URLs during parse, validation, or rendering.
- Treat optional extensions as untrusted and isolate failures behind typed boundaries.

## Filesystem adapters

CLI writes are explicit, use the requested target only, and do not overwrite input unless an
in-place action is explicitly selected. Temporary files use the platform temporary
directory. Migration dry-run performs no writes.

## Dependency and release review

CI builds from the lockfile, audits the committed dependency diff, builds artifacts from a
clean tag, and publishes hashes and attestations. PNG dependencies remain optional so
non-rendering consumers do not inherit native graphics risk.

## Reporting

Do not disclose a suspected vulnerability in a public issue before maintainers have a
reasonable opportunity to assess it. Use the repository host's private vulnerability
reporting channel when enabled. Include affected version, minimal reproduction, impact, and
any safe mitigation.
