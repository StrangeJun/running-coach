# Definition of done

A task is complete only when:

- Requested scope is implemented, with no unrelated scope added.
- Relevant tests pass; backend tests pass when backend changes apply.
- Frontend typecheck and lint pass when frontend changes apply.
- The diff contains no credentials, Garmin tokens, FIT files, GPS data, or personal activity data.
- Documentation reflects any architecture or material project-state changes.
- Known limitations and any unavailable checks are reported.

Use existing check commands. If required tooling is absent or checks fail, state that validation is incomplete rather than claiming they passed. Documentation-only changes require content, links, diff, and ignore-rule verification; application checks do not apply.
