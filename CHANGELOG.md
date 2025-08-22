# Changelog

All notable changes to the Telegram Moderation Bot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2025-08-22

### Video Analysis Enhancement
- **Frame extraction**: Added intelligent video frame extraction using OpenCV
- **Video content analysis**: Implemented AI-powered analysis of video frames for NSFW detection
- **Smart frame selection**: Strategic frame sampling for comprehensive video analysis
- **Performance optimization**: Efficient frame extraction with size limits and cleanup
- **Enhanced video moderation**: Both basic and advanced video moderation systems now analyze actual content

### Technical Improvements
- Added 13 comprehensive video moderation tests
- Added 28 additional tests for edge cases and error handling
- Improved overall test coverage to 75% (164 tests total)
- Enhanced error handling for video processing
- Comprehensive coverage of image and video detection scenarios
- Enhanced resource cleanup for temporary files
- Support for various video durations with adaptive frame extraction

## [2.1.0] - 2025-08-22

### Security Improvements
- **Token encryption**: Implemented secure token storage with encryption using Fernet cipher
- **ReDoS prevention**: Added regex pattern validation to prevent Regular Expression Denial of Service attacks
- **Input validation**: Added size limits for messages (4KB), images (10MB), and videos (50MB)
- **Path traversal protection**: Implemented path sanitization to prevent directory traversal attacks
- **Rate limiting**: Added configurable rate limiter with burst support to prevent abuse

### Added
- Environment variable support for bot token (`TELEGRAM_BOT_TOKEN`)
- LRU cache implementation for improved performance
- Concurrent execution for AI models using thread pool executor
- Improved keyword matching with word boundaries
- Health check endpoint for monitoring bot status
- Configuration constants for all moderation thresholds
- Resource cleanup on bot shutdown (ThreadPoolExecutor)
- Security module with TokenManager, InputValidator, and RateLimiter classes
- Comprehensive security test suite (17 new tests)

### Changed
- Enhanced error handling with more descriptive error messages
- Bot now requires valid configuration to start (no silent fallback)
- Optimized cache management with bounded size (max 1000 entries)
- Pinned all dependency versions for production stability
- Extracted magic numbers to ModerationThresholds configuration class

### CI/CD & DevOps
- Complete GitHub Actions workflow for automated testing and deployment
- GitLab CI pipeline configuration with security scanning
- Docker containerization with multi-stage builds
- Kubernetes deployment manifests with HPA and health checks
- Pre-commit hooks for code quality enforcement
- Makefile for common development tasks
- Automated deployment scripts with rollback capability
- Comprehensive CI/CD documentation

### Fixed
- Added missing test fixtures (`temp_models_dir` and `model_manager`) to `TestModelManagerEdgeCases` class in test_model_manager.py
- All 20 model manager tests now pass successfully
- Fixed asyncio deprecation warnings in RateLimiter
- Fixed test compatibility issues with security improvements

## [2.0.0] - 2025-08-21

### Added
- Production-ready AI models integration for advanced content moderation
- Custom rule parser for flexible moderation policies
- Comprehensive test suite with 81% code coverage
- Model manager for downloading and managing AI models
- Support for toxicity detection, hate speech detection, and spam filtering
- System requirements validation for AI models

### Changed
- Major upgrade to moderation capabilities with AI-powered analysis
- Enhanced test coverage and reliability

## [1.0.0] - 2025-08-21

### Added
- Initial release of user-friendly Telegram Moderation Bot
- GUI interface for easy configuration and management
- Basic content moderation features:
  - Spam and ads removal
  - Harassment and bullying blocking
  - Adult content filtering
  - Excessive caps detection
  - Hate speech detection
- Setup wizard for non-technical users
- Windows batch files and Unix shell scripts for easy installation
- Local processing for privacy and security
- Real-time message processing
- Comprehensive logging system
- Configurable violation thresholds