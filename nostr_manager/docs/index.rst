===============
Nostr Manager
===============

Overview
========

Nostr Manager is a comprehensive Nostr client module for Odoo that provides complete management of Nostr identities, keys, and relay infrastructure.

Features
========

Key Management
--------------

* **Secure Key Generation**: 2-step wizard for generating new Nostr key pairs
* **Vault Integration**: Private keys stored securely using vault_connector
* **Address Book**: Collect and manage public keys (npubs) for contacts
* **Partner Integration**: Associate keys with business partners
* **Import Support**: Import existing nsec/npub keys

Relay Management
----------------

* **12+ Default Relays**: Pre-configured popular public Nostr relays
* **Connection Testing**: Test relay connectivity with NIP-11 support
* **Read/Write Configuration**: Configure relays for reading vs publishing
* **Usage Statistics**: Track events read/written per relay
* **Custom Relays**: Add your own private or specialized relays

Business Integration
--------------------

* **Partner Association**: Link Nostr identities to business contacts
* **Activity Tracking**: Full chatter integration with change tracking
* **File Attachments**: Attach QR codes, backups, documentation
* **Notes & Documentation**: Rich text notes for each key and relay

Security
--------

* **One-Time Display**: Private keys shown only once during generation
* **Vault Storage**: Private keys never stored in database
* **Access Control**: User vs admin permissions
* **Audit Trail**: Complete activity logging

Nostr Key Formats
=================

Understanding Nostr key formats is essential for proper key management:

nsec (Private Key)
------------------

**Format**: ``nsec1...`` (63 characters total)

* **Purpose**: Your secret private key used for signing messages and proving identity
* **Encoding**: bech32 encoding with 'nsec' prefix
* **Length**: 63 characters (nsec1 + 58 bech32-encoded characters)
* **Security**: Must be kept absolutely secret - anyone with this can impersonate you
* **Example**: ``nsec1vl029mgpspedva04g90vltkh6fvh240zqtv9k0t9af8935ke9laqsnlfe5``

.. warning::
   Never share your nsec private key. Store it securely offline.

npub (Public Key)
-----------------

**Format**: ``npub1...`` (63 characters total)

* **Purpose**: Your public identity/address that others use to find and verify you
* **Encoding**: bech32 encoding with 'npub' prefix
* **Length**: 63 characters (npub1 + 58 bech32-encoded characters)
* **Security**: Safe to share publicly - this is your Nostr "address"
* **Example**: ``npub1sg6plzptd64u62a878hep2kev88swjh3tw00gjsfl8f237lmu63q0uf63m``

.. note::
   Your npub is derived mathematically from your nsec using secp256k1 elliptic curve cryptography.

Key Relationship
----------------

.. code-block:: text

   nsec (private) --[secp256k1]--> npub (public)

   ✓ nsec → npub (always possible)
   ✗ npub → nsec (cryptographically impossible)

**Import Scenarios**:

* **Import nsec**: System derives the matching npub automatically
* **Import npub**: Public key only - cannot sign messages, read-only contact

Installation
============

Prerequisites
-------------

1. **vault_connector** module installed and configured
2. HashiCorp Vault server accessible
3. Proper vault environment variables set

Install Module
--------------

.. code-block:: bash

   odoo-bin -d database_name -i nostr_manager

Usage
=====

Generate New Key
----------------

1. Go to **Nostr > Generate New Key**
2. Enter key name and optional partner
3. Click "Generate Keys"
4. **Save the displayed private key (nsec) securely**
5. Share your public key (npub) as needed

Manage Relays
-------------

1. Go to **Nostr > Relays**
2. Review pre-configured public relays
3. Test connections using "Test Connection" button
4. Add custom relays as needed
5. Configure read/write settings per relay

Partner Integration
-------------------

1. Open any partner record
2. Go to "Nostr Keys" tab
3. Generate or associate keys with the partner
4. Set active key for primary identity

Configuration
=============

Vault Connector
---------------

Ensure vault_connector is properly configured with:

* ``VAULT_ADDR``: Vault server URL
* ``VAULT_TOKEN``: Authentication token
* Vault KV store accessible

Relay Defaults
--------------

The module includes these default relays:

* Damus (wss://relay.damus.io)
* Nostr.band (wss://nostr.band)
* nos.lol (wss://nos.lol)
* Primal (wss://relay.primal.net)
* Snort (wss://relay.snort.social)
* And 7 more...

.. note::
   All default relays are configured with ``noupdate="1"`` to preserve user customizations during module upgrades.

Architecture
============

Models
------

**nostr.key**
  Key pairs with vault integration

**nostr.relay**
  Relay server management

**res.partner**
  Extended with Nostr key fields

Security
--------

* Private keys stored in HashiCorp Vault
* UUID-based vault key references
* Field-level access controls
* Change tracking and audit trail

Development
===========

Key Generation Flow
-------------------

1. User enters name/partner in wizard
2. System generates secp256k1 key pair
3. Private key stored in vault with UUID reference
4. Public key derived and displayed
5. User copies and saves keys securely

Cryptographic Implementation
----------------------------

The module uses the following cryptographic implementations:

* **secp256k1** library for elliptic curve key derivation and signing
* **Built-in bech32** encoder/decoder for npub/nsec format compliance
* **Secure key generation** using Python's `secrets` module for cryptographic randomness

Installation requires the `secp256k1` Python library:

.. code-block:: bash

   pip install secp256k1

.. seealso::
   * :doc:`configuration`
   * :doc:`security`
   * :doc:`api`
