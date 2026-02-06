# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-02-06

### Added
- Initial release of `py-rate-guard`.
- Core rate limiting engine with Redis support.
- Strategies: Sliding Window, Token Bucket, Fixed Window, Leaky Bucket.
- Framework adapters for FastAPI and Django.
- Hierarchical rule enforcement.
- Key resolvers for IP, Headers, and Users.
- Graceful degradation with in-memory fallback.
- Structured logging and Prometheus metrics.
- Comprehensive test suite and examples.
