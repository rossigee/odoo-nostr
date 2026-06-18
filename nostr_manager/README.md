# Nostr Manager for Odoo

[![Test Status](https://github.com/YOUR_ORG/nostr-manager/workflows/Odoo%20Module%20Tests/badge.svg)](https://github.com/YOUR_ORG/nostr-manager/actions)
[![codecov](https://codecov.io/gh/YOUR_ORG/nostr-manager/branch/16.0/graph/badge.svg)](https://codecov.io/gh/YOUR_ORG/nostr-manager)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Odoo Version](https://img.shields.io/badge/Odoo-17.0-purple.svg)](https://github.com/odoo/odoo/tree/17.0)

A comprehensive Nostr client module for Odoo that provides secure key management, relay infrastructure, and business partner integration for the decentralized Nostr protocol.

## 🔥 Features

### 🔐 Secure Key Management
- **2-Step Key Generation Wizard**: User-friendly guided key creation
- **2-Step Import Wizard**: Import existing nsec/npub keys safely  
- **Vault Integration**: Private keys stored securely using vault_connector
- **One-Time Display**: Private keys shown only once during generation
- **Address Book**: Collect and manage public keys (npubs) for contacts

### 🌐 Relay Management
- **12+ Default Relays**: Pre-configured popular public Nostr relays
- **Connection Testing**: Test relay connectivity with NIP-11 support
- **Read/Write Configuration**: Configure relays for reading vs publishing
- **Usage Statistics**: Track events read/written per relay
- **Custom Relays**: Add your own private or specialized relays

### 🏢 Business Integration
- **Partner Association**: Link Nostr identities to business contacts
- **Activity Tracking**: Full chatter integration with change tracking
- **File Attachments**: Attach QR codes, backups, documentation
- **Notes & Documentation**: Rich text notes for each key and relay

### 🔒 Production-Ready Security
- **secp256k1 Cryptography**: Proper elliptic curve operations
- **bech32 Encoding**: Standard Nostr key format compliance
- **Access Controls**: User vs admin permissions
- **Audit Trail**: Complete activity logging

## 📋 Requirements

- **Odoo**: 17.0+
- **Python**: 3.9+
- **Dependencies**:
  - `secp256k1` (cryptographic operations)
  - `vault_connector` (secure storage)

## 🚀 Installation

### 1. Install Dependencies

```bash
# Install cryptographic library
pip install secp256k1

# Optional: Install fallback library for Windows
pip install coincurve
```

### 2. Install vault_connector

```bash
# Clone and install vault_connector module
git clone https://github.com/YOUR_ORG/vault-connector.git
# Copy to your Odoo addons directory
```

### 3. Install Nostr Manager

```bash
# Download latest release
wget https://github.com/YOUR_ORG/nostr-manager/releases/latest/download/nostr_manager.tar.gz
tar -xzf nostr_manager.tar.gz

# Copy to Odoo addons directory
cp -r nostr_manager /path/to/odoo/addons/

# Install via Odoo
odoo-bin -d your_database -i nostr_manager
```

## 🎯 Quick Start

### Generate Your First Nostr Key

1. Navigate to **Nostr > Generate New Key**
2. Enter a descriptive name and optional partner
3. Click "Generate Keys"
4. **⚠️ IMPORTANT**: Copy and save the displayed private key (nsec) securely
5. Share your public key (npub) as needed

### Import Existing Keys

1. Navigate to **Nostr > Import Existing Key**
2. Enter key name and optional partner
3. Paste your existing nsec (private) or npub (public) key
4. Click "Validate & Continue" to confirm
5. Click "Import Key" to complete

### Manage Relays

1. Navigate to **Nostr > Relays**
2. Review pre-configured public relays
3. Test connections using "Test Connection" button
4. Add custom relays as needed
5. Configure read/write settings per relay

## 📖 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Getting Started](docs/index.rst)**: Installation and basic usage
- **[Security Guide](docs/security.rst)**: Security architecture and best practices  
- **[API Reference](docs/api.rst)**: Complete model and method documentation
- **[Configuration](docs/configuration.rst)**: Advanced configuration options

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
odoo-bin -d test_db --test-enable --stop-after-init -i nostr_manager

# Run specific test class
python -m pytest addons/nostr_manager/tests/test_nostr_cryptography.py -v

# Run with coverage
coverage run odoo-bin -d test_db --test-enable --stop-after-init -i nostr_manager
coverage report --include="addons/nostr_manager/*"
```

## 🤝 Contributing

We welcome contributions! Please:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Install** pre-commit hooks (`pre-commit install`)
4. **Make** your changes with tests
5. **Commit** your changes (`git commit -m 'Add amazing feature'`)
6. **Push** to the branch (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

### Development Setup

```bash
# Clone repository
git clone https://github.com/YOUR_ORG/nostr-manager.git
cd nostr-manager

# Install development dependencies
pip install pre-commit pytest coverage

# Install pre-commit hooks
pre-commit install

# Run pre-commit checks
pre-commit run --all-files
```

## 🐛 Bug Reports

Found a bug? Please [open an issue](https://github.com/YOUR_ORG/nostr-manager/issues) with:

- **Environment**: Odoo version, Python version, OS
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Error messages** (if any)
- **Screenshots** (if helpful)

## 🔒 Security

Security is paramount for cryptographic software. Please:

- **Report security issues** privately to [security@example.com](mailto:security@example.com)
- **Use strong passwords** for your Odoo instance
- **Keep dependencies updated** regularly
- **Follow security best practices** in our [Security Guide](docs/security.rst)

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Nostr Protocol**: [https://github.com/nostr-protocol/nostr](https://github.com/nostr-protocol/nostr)
- **Odoo Community**: [https://www.odoo.com/page/community](https://www.odoo.com/page/community)
- **secp256k1 Library**: [https://github.com/bitcoin-core/secp256k1](https://github.com/bitcoin-core/secp256k1)

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/YOUR_ORG/nostr-manager/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_ORG/nostr-manager/discussions)
- **Community**: Join the conversation on Nostr!

---

**Built with ❤️ for the Nostr and Odoo communities**
