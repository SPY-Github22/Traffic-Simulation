---
name: testing_validation
description: Skill to validate correctness and run automated tests before finalizing a task.
---

# Testing & Validation

## Responsibilities
- Validate code correctness through automated testing.
- Catch conflicts and mistakes before presenting the work to the user.

## Instructions
1. For every piece of implemented functionality, ensure a corresponding test exists or is written.
2. Execute the test suite using the appropriate framework.
3. If tests fail, analyze the output, fix the code, and log the failure using the error tracking skill.
4. Do not consider a task complete until all tests pass and validation is successful. Never present unverified or broken code to the user.
