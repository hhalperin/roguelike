---
description: Scaffold a new API endpoint together with its test. Use when adding a route, handler, or service method to a backend.
---

# Add an endpoint

1. Find the existing endpoint/route pattern and copy its structure — router
   registration, request/response models, error handling, and typing.
2. Implement the handler with full type hints and input validation.
3. Add a matching test that covers the happy path plus at least one error
   case, following the repo's existing test style.
4. Run the test suite and confirm the new test passes before finishing.
