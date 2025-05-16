# Changelog

All notable changes to the MkDocs Protobuf Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Changed
- Improved i18n support to automatically detect the presence of the mkdocs-static-i18n plugin without requiring explicit configuration

## [0.1.0] - 2025-05-16

### Added
- Initial release with core functionality
- Support for converting .proto files to Markdown documentation
- File cache system to track which proto files need conversion
- Navigation handling that respects custom navigation structures
- Support for mkdocs-static-i18n plugin for multilingual documentation
- Created i18n_support.py module to handle internationalization features
- Added GitHub Actions workflows for testing, documentation, releases and version bumping

### Changed
- Refactored navigation handling to support i18n plugin language structures
- Updated documentation to include i18n compatibility information

