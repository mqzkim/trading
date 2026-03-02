# Code Quality Rules

## Simplicity

- Three similar lines are better than a premature abstraction
- Do not create helpers or utilities for one-time operations
- Do not design for hypothetical future requirements
- The right amount of complexity is the minimum needed for the current task

## Security

- Never hardcode secrets, tokens, or passwords
- Validate all external input (user input, API responses)
- Trust internal code and framework guarantees -- only validate at system boundaries
- Use parameterized queries for database operations
- Sanitize output to prevent XSS

## Error Handling

- Fail fast with descriptive error messages
- Do not catch errors just to re-throw them
- Log errors with enough context to debug (what happened, what was expected, relevant IDs)
- Avoid silent failures -- if something goes wrong, make it visible

## Dependencies

- Prefer standard library over third-party packages for simple tasks
- Check existing dependencies before adding new ones
- Pin dependency versions for reproducible builds
