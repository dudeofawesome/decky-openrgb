# Architecture

## Purpose

This specification records project-wide technical decisions that constrain how
the feature specifications are implemented without changing their user-visible
behavior.

## Frontend

1. The frontend must use Effect (`effect`) for application logic, including
   asynchronous backend interactions, error handling, and state transitions.
2. Decky and React integration should remain at the UI boundary, with UI
   components executing or subscribing to Effect-based application logic.

## Acceptance Criteria

- **ARCH-001:** The frontend declares `effect` as a runtime dependency, and its
  backend interactions, expected errors, and asynchronous state transitions are
  implemented with Effect rather than ad hoc Promise chains or thrown errors.
