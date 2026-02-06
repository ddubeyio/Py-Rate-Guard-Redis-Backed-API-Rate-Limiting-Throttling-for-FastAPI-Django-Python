# Contributing to py-rate-guard

First of all, thank you for considering contributing to `py-rate-guard`! It's people like you who make the open-source community such an amazing place to learn, inspire, and create.

## Build and Test

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/py-rate-guard.git
   cd py-rate-guard
   ```

2. Install dependencies:
   ```bash
   pip install -e ".[dev,fastapi,django]"
   ```

3. Run tests:
   ```bash
   pytest
   ```

## Development Guidelines

- **Code Style**: We use `black` for formatting and `isort` for sorting imports. Please run these before submitting a PR.
- **Type Hints**: All new code must be fully type-hinted.
- **Atomic Operations**: If adding a new rate-limiting algorithm, it MUST be implemented as a Redis Lua script to ensure atomicity in distributed environments.
- **Tests**: Every new feature or bug fix should come with corresponding tests.

## Pull Request Process

1. Fork the repo and create your branch from `main`.
2. Commit your changes with descriptive commit messages.
3. Ensure the test suite passes.
4. Update the documentation if you've added or changed features.
5. Submit a pull request!

## Security 

If you discover a security vulnerability, please send an e-mail to security@example.com instead of opening a public issue.

## License

By contributing, you agree that your contributions will be licensed under its MIT License.
