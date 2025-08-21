# Changelog

All notable changes to the Telegram Moderation Bot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Added missing test fixtures (`temp_models_dir` and `model_manager`) to `TestModelManagerEdgeCases` class in test_model_manager.py
- All 20 model manager tests now pass successfully

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