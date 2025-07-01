# Changelog

All notable changes to the Nostr Manager module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2025-01-XX

### Added
- **Core Key Management**
  - 2-step key generation wizard with secure one-time private key display
  - 2-step import wizard for existing nsec/npub keys
  - Vault integration for secure private key storage using UUID references
  - Support for both private key management (nsecs) and address book (npubs)
  - Unique public key constraint to prevent duplicates

- **Cryptographic Implementation**
  - Production-ready secp256k1 elliptic curve operations
  - Complete bech32 encoding/decoding for nsec/npub formats
  - Secure random key generation using Python's `secrets` module
  - Fallback support for coincurve library (Windows compatibility)

- **Relay Management**
  - 12+ pre-configured popular public Nostr relays
  - Connection testing with NIP-11 relay information support
  - Read/write configuration per relay
  - Usage statistics tracking (events read/written)
  - Custom relay addition and management

- **Business Integration**
  - Partner association for business contacts
  - Activity tracking with full chatter integration
  - File attachments support (QR codes, backups, documentation)
  - Rich text notes for keys and relays

- **User Interface**
  - Top-level "Nostr" menu with organized submenus
  - Color-coded list views (green=has private key, blue=public only)
  - Copy-enabled fields using CopyClipboardChar widget
  - Form-level security with proper access controls

- **Security & Access Control**
  - Field-level access controls (users vs administrators)
  - Complete audit trail with change tracking
  - One-time private key display pattern
  - Vault connectivity validation

- **Testing & Quality**
  - Comprehensive test suite (50+ test cases)
  - Cryptographic regression tests
  - Key management workflow tests
  - Wizard functionality tests
  - Relay management tests

- **Development & CI/CD**
  - GitHub Actions workflow for automated testing
  - Pre-commit hooks for code quality
  - Security scanning with bandit
  - Coverage reporting with codecov
  - Automated release workflow

- **Documentation**
  - Complete reStructuredText documentation
  - Security guide with best practices
  - API reference with model documentation
  - Installation and usage instructions
  - Contributing guidelines

### Technical Details
- **Dependencies**: Odoo 16.0+, vault_connector, secp256k1
- **Models**: nostr.key, nostr.relay, res.partner extensions
- **Wizards**: nostr.key.generator.wizard, nostr.key.import.wizard
- **Security**: AGPL-3 license, production cryptography
- **Compatibility**: Linux, macOS, Windows (with coincurve)

[Unreleased]: https://github.com/YOUR_ORG/nostr-manager/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/YOUR_ORG/nostr-manager/releases/tag/v1.0.0
