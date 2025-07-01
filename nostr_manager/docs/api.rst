==========
API Reference
==========

This document provides detailed API reference for the Nostr Manager module models and methods.

Nostr Key Format Reference
===========================

The Nostr protocol uses specific key formats based on bech32 encoding:

nsec Format (Private Keys)
---------------------------

.. code-block:: text

   Format: nsec1{58-character-bech32-string}
   Total Length: 63 characters
   Example: nsec1vl029mgpspedva04g90vltkh6fvh240zqtv9k0t9af8935ke9laqsnlfe5

**Characteristics:**
  * Contains 32 bytes of private key data
  * Encoded using bech32 with 'nsec' HRP (Human Readable Part)
  * Used for signing Nostr events and proving identity
  * Must be kept secret at all times

npub Format (Public Keys)
--------------------------

.. code-block:: text

   Format: npub1{58-character-bech32-string}
   Total Length: 63 characters
   Example: npub1sg6plzptd64u62a878hep2kev88swjh3tw00gjsfl8f237lmu63q0uf63m

**Characteristics:**
  * Contains 32 bytes of public key data (x-coordinate of secp256k1 point)
  * Encoded using bech32 with 'npub' HRP
  * Safe to share publicly - serves as your Nostr address
  * Cannot be used to derive the private key

Cryptographic Relationship
---------------------------

.. code-block:: text

   Private Key (32 bytes) --[secp256k1 point multiplication]--> Public Key (32 bytes)
                nsec                                                        npub

The transformation is one-way: you can always derive npub from nsec, but never nsec from npub.

Models Overview
===============

The module provides three main models:

* ``nostr.key`` - Manages Nostr key pairs
* ``nostr.relay`` - Manages Nostr relay connections
* ``res.partner`` - Extended with Nostr functionality

nostr.key Model
===============

Core model for managing Nostr key pairs with secure vault integration.

Fields
------

.. py:attribute:: name

   :type: Char
   :required: True
   :tracking: True

   Descriptive name for the key pair

.. py:attribute:: partner_id

   :type: Many2one('res.partner')
   :tracking: True

   Optional partner associated with this key

.. py:attribute:: key_type

   :type: Selection
   :default: 'generated'

   Type of key: 'generated' or 'imported'

.. py:attribute:: public_key

   :type: Char
   :readonly: True

   Public key in npub format

.. py:attribute:: public_key_hex

   :type: Char
   :readonly: True

   Public key in hexadecimal format

.. py:attribute:: vault_key_id

   :type: Char
   :readonly: True

   UUID reference for private key in vault

.. py:attribute:: has_private_key

   :type: Boolean
   :computed: True
   :stored: True

   Whether this key has an associated private key

.. py:attribute:: notes

   :type: Text
   :tracking: True

   Additional notes about the key pair

Methods
-------

.. py:method:: generate_key_pair(partner_id, name)

   Generate a new Nostr key pair

   :param int partner_id: ID of associated partner (optional)
   :param str name: Descriptive name for the key pair
   :returns: Created nostr.key record
   :rtype: nostr.key

   Generates a new secp256k1 key pair, stores the private key securely in vault,
   and returns the created record with public key information.

.. py:method:: _store_private_key_in_vault(private_key_hex, partner_id, name)

   Store private key in vault

   :param str private_key_hex: Private key in hexadecimal format
   :param int partner_id: Associated partner ID
   :param str name: Key name for vault storage
   :returns: Vault key UUID
   :rtype: str

   Internal method that stores the private key in HashiCorp Vault and returns
   a UUID reference for future retrieval.

.. py:method:: _derive_public_key(private_key_hex)

   Derive public key from private key using secp256k1 elliptic curve cryptography

   :param str private_key_hex: Private key in hexadecimal
   :returns: Public key in hexadecimal
   :rtype: str

   Uses secp256k1 library for proper elliptic curve cryptographic operations.

.. py:method:: _hex_to_npub(public_key_hex)

   Convert hex public key to npub format using bech32 encoding

   :param str public_key_hex: Public key in hexadecimal
   :returns: Public key in npub format
   :rtype: str

   Uses standard bech32 encoding with 'npub' human-readable prefix.

nostr.relay Model
=================

Model for managing Nostr relay server connections.

Fields
------

.. py:attribute:: name

   :type: Char
   :required: True
   :tracking: True

   Descriptive name for the relay

.. py:attribute:: url

   :type: Char
   :required: True
   :tracking: True

   WebSocket URL of the relay (wss:// or ws://)

.. py:attribute:: description

   :type: Text

   Description of the relay and its purpose

.. py:attribute:: is_active

   :type: Boolean
   :default: True
   :tracking: True

   Whether this relay is currently active

.. py:attribute:: is_read

   :type: Boolean
   :default: True

   Use this relay for reading events

.. py:attribute:: is_write

   :type: Boolean
   :default: True

   Use this relay for publishing events

.. py:attribute:: connection_status

   :type: Selection
   :readonly: True
   :default: 'unknown'

   Current connection status: 'unknown', 'connected', 'disconnected', 'error'

.. py:attribute:: relay_info

   :type: Text
   :readonly: True

   NIP-11 relay information document

.. py:attribute:: supported_nips

   :type: Char
   :readonly: True

   Comma-separated list of supported NIPs

.. py:attribute:: event_count_read

   :type: Integer
   :readonly: True
   :default: 0

   Number of events read from this relay

.. py:attribute:: event_count_write

   :type: Integer
   :readonly: True
   :default: 0

   Number of events written to this relay

Methods
-------

.. py:method:: action_test_connection()

   Test connection to the relay

   :returns: Notification action
   :rtype: dict

   Tests connectivity to the relay server and updates connection status.
   Also attempts to retrieve NIP-11 relay information if available.

.. py:method:: increment_read_count()

   Increment read event counter

   Call this method when an event is successfully read from the relay.

.. py:method:: increment_write_count()

   Increment write event counter

   Call this method when an event is successfully written to the relay.

Constraints
-----------

.. py:attribute:: _sql_constraints

   * ``unique_url``: Relay URL must be unique across all relays

Validation
----------

.. py:method:: _check_url_format()

   Validates that relay URLs start with 'ws://' or 'wss://'

res.partner Model Extensions
============================

Extensions to the standard partner model for Nostr integration.

Added Fields
------------

.. py:attribute:: nostr_key_ids

   :type: One2many('nostr.key', 'partner_id')

   All Nostr keys associated with this partner

.. py:attribute:: nostr_key_count

   :type: Integer
   :computed: True

   Count of associated Nostr keys

.. py:attribute:: active_nostr_key_id

   :type: Many2one('nostr.key')

   Primary active Nostr key for this partner

Added Methods
-------------

.. py:method:: action_view_nostr_keys()

   Open list of partner's Nostr keys

   :returns: Window action to display keys
   :rtype: dict

.. py:method:: generate_nostr_key(key_name=None)

   Generate new Nostr key for this partner

   :param str key_name: Optional name for the key
   :returns: Created key record
   :rtype: nostr.key

Wizard Models
=============

nostr.key.wizard Model
----------------------

Transient model for the 2-step key generation wizard.

Fields
~~~~~~

.. py:attribute:: name

   :type: Char
   :required: True

   Name for the new key pair

.. py:attribute:: partner_id

   :type: Many2one('res.partner')

   Optional partner to associate with the key

.. py:attribute:: generated_nsec

   :type: Char
   :readonly: True

   Generated private key (displayed once)

.. py:attribute:: generated_npub

   :type: Char
   :readonly: True

   Generated public key

.. py:attribute:: step

   :type: Selection
   :default: 'step1'

   Current wizard step: 'step1' or 'step2'

Methods
~~~~~~~

.. py:method:: action_generate_keys()

   Generate keys and move to step 2

   :returns: Wizard action for step 2
   :rtype: dict

.. py:method:: action_finish()

   Complete wizard and open created key

   :returns: Action to view the created key
   :rtype: dict

.. py:method:: action_back()

   Return to step 1

   :returns: Wizard action for step 1
   :rtype: dict

Usage Examples
==============

Generate Key Programmatically
------------------------------

.. code-block:: python

   # Generate a new key pair
   nostr_key = env['nostr.key'].generate_key_pair(
       partner_id=partner.id,  # Optional
       name="My Test Key"
   )

   print(f"Generated key: {nostr_key.public_key}")

Test Relay Connection
---------------------

.. code-block:: python

   # Test all active relays
   active_relays = env['nostr.relay'].search([('is_active', '=', True)])
   for relay in active_relays:
       result = relay.action_test_connection()
       print(f"Relay {relay.name}: {relay.connection_status}")

Partner Key Management
----------------------

.. code-block:: python

   # Get partner's active key
   partner = env['res.partner'].browse(partner_id)
   if partner.active_nostr_key_id:
       active_key = partner.active_nostr_key_id
       print(f"Active key: {active_key.public_key}")

   # Generate new key for partner
   new_key = partner.generate_nostr_key("Business Key")

Error Handling
==============

Vault Connectivity
------------------

.. code-block:: python

   from odoo.exceptions import ValidationError

   try:
       key = env['nostr.key'].generate_key_pair(None, "Test Key")
   except ValidationError as e:
       if "Vault is not accessible" in str(e):
           # Handle vault connectivity issues
           pass

Key Import Validation
---------------------

.. code-block:: python

   # Invalid key import will raise ValidationError
   try:
       key = env['nostr.key'].create({
           'name': 'Imported Key',
           'import_nsec': 'invalid_key_format'
       })
   except ValidationError as e:
       # Handle invalid key format
       pass
