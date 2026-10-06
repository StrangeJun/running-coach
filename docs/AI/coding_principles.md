# Coding principles

- Prefer simple concrete code before abstractions; introduce abstractions only for demonstrated needs.
- Keep functions and modules small, focused, and easy to understand.
- Respect the domain boundaries in `../architecture.md`; make inputs, outputs, units, and missing-data behavior explicit.
- Test deterministic domain logic with synthetic fixtures and meaningful expected results.
- Avoid unrelated refactors and new dependencies without a task-driven need.
- Preserve existing behavior unless the task requires a change.
- Handle failures explicitly; keep error messages useful without exposing sensitive values.
