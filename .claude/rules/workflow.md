# Development Workflow Rules

## Before Writing Code

- Read the relevant source files first -- never modify code you haven't read
- Check for existing implementations before creating new ones
- Understand the test coverage of the area you're changing

## While Writing Code

- Make the smallest change that solves the problem
- Do not add features, refactor, or "improve" code beyond the request
- Do not add comments to code you didn't change
- Do not add error handling for scenarios that cannot happen
- Prefer editing existing files over creating new ones

## After Writing Code

- Run the relevant tests (single file preferred over full suite)
- Run typecheck/lint to catch issues early
- Verify the change works as expected before declaring done
- If tests fail, fix the root cause -- do not retry blindly

## Git Discipline

- Stage specific files, not `git add -A`
- Never commit `.env`, credentials, or secrets
- Never force-push without explicit permission
- Never amend published commits
- Commit messages follow conventional commits format
