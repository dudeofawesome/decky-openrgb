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

## Backend

1. All project-owned Python backend modules must reside beneath `/py_modules`.
   The Decky-required `/main.py` file is the entrypoint exception and should
   delegate backend logic to modules in `/py_modules`. Python tests remain in
   `/tests`.
