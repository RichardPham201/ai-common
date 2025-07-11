# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-07-11

### Added
- Initial release of ai-common package
- Queue services module with abstract QueueService interface
- RabbitMQ implementation of queue service
- GPU memory utilities for monitoring and cleanup
- Image processing utilities for format conversions
- Base processor pattern with singleton and lazy loading
- Comprehensive logging support
- Error handling and recovery mechanisms
- Context manager support for resource management

### Features
- **Queue Services**: Complete RabbitMQ integration with connection management
- **GPU Memory Management**: Automatic memory monitoring and cleanup utilities
- **Image Processing**: Support for PIL, OpenCV, numpy format conversions
- **AI Model Patterns**: Base processor class with common patterns
- **Cross-platform compatibility**: Works on Windows, Linux, macOS
- **Optional dependencies**: Only install what you need

### Documentation
- Complete API documentation
- Quick start guide with examples
- Migration guide for existing projects
- Comprehensive README with usage examples
