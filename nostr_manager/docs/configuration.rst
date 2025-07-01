=============
Configuration
=============

This document describes how to configure the Nostr Manager module for optimal use.

Prerequisites
=============

Vault Connector
---------------

The Nostr Manager module requires the ``vault_connector`` module to be installed and properly configured.

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Set the following environment variables for vault connectivity:

.. code-block:: bash

   export VAULT_ADDR="https://vault.example.com:8200"
   export VAULT_TOKEN="your-vault-token"
   export VAULT_SKIP_VERIFY="true"  # Optional, for development only
   export VAULT_KV_STORE="secret"   # Optional, default KV store name

Vault Permissions
~~~~~~~~~~~~~~~~~

Ensure your vault token has the following permissions:

* ``secret/data/*`` - Read/Write access to secret paths
* ``secret/metadata/*`` - Metadata operations

Test vault connectivity:

.. code-block:: bash

   curl -H "X-Vault-Token: $VAULT_TOKEN" \
        -X GET $VAULT_ADDR/v1/secret/data/test

Module Installation
===================

Install Dependencies
--------------------

1. Install vault_connector module first
2. Verify vault connectivity
3. Install nostr_manager module

.. code-block:: bash

   # Install vault_connector
   odoo-bin -d database_name -i vault_connector

   # Verify vault works
   # Test through Odoo interface

   # Install nostr_manager
   odoo-bin -d database_name -i nostr_manager

Default Data
============

Upon installation, the module automatically creates 12 popular public Nostr relays:

Relay Configuration
-------------------

========================================  ===============================
Relay Name                                URL
========================================  ===============================
Damus                                     wss://relay.damus.io
Nostr.band                                wss://nostr.band
nos.lol                                   wss://nos.lol
Primal                                    wss://relay.primal.net
Snort                                     wss://relay.snort.social
WellOrder                                 wss://nostr-pub.wellorder.net
Bitcoiner Social                          wss://nostr.bitcoiner.social
Orange Pill                               wss://nostr.orangepill.dev
Nostr Wine                                wss://relay.nostr.wine
FMT Relay                                 wss://nostr-relay.fmt.wiz.biz
Purple Pages                              wss://purplepag.es
Relay.nostr.info                          wss://relay.nostr.info
========================================  ===============================

All relays are configured with:

* ``is_active = True``
* ``is_read = True``
* ``is_write = True``
* ``noupdate = 1`` (preserves customizations during upgrades)

User Permissions
================

Default Access Levels
----------------------

**Regular Users (base.group_user)**
  * Read, write, create keys and relays
  * Cannot delete records
  * Full access to wizards

**System Administrators (base.group_system)**
  * Full access including delete permissions
  * Can modify system-level settings
  * Access to vault key IDs (for debugging)

Custom Relay Setup
==================

Adding Private Relays
---------------------

To add your own relays:

1. Go to **Nostr > Relays**
2. Click **Create**
3. Fill in the required fields:

   * **Name**: Descriptive name for the relay
   * **URL**: WebSocket URL (must start with ``wss://`` or ``ws://``)
   * **Description**: Purpose and notes
   * **Configuration**: Set read/write permissions

4. Test the connection using **Test Connection** button

Relay URL Validation
~~~~~~~~~~~~~~~~~~~~~

The system validates relay URLs to ensure they:

* Start with ``wss://`` (secure) or ``ws://`` (insecure)
* Are unique across all relays
* Follow proper WebSocket URL format

.. warning::
   Using ``ws://`` (unencrypted) relays is not recommended for production use.

Partner Integration
===================

Enabling Partner Keys
---------------------

Partners can have associated Nostr keys:

1. Open partner record
2. Navigate to **Nostr Keys** tab
3. Generate new keys or view existing associations
4. Set **Active Nostr Key** for primary identity

This integration allows:

* Business partner Nostr identity management
* Contact-specific key associations
* Partner-based key filtering and reporting

Security Configuration
======================

Key Storage Security
--------------------

* **Private keys** are never stored in the Odoo database
* All private keys are stored in HashiCorp Vault with UUID references
* **Public keys** are stored in the database for performance
* Private keys are displayed only once during generation

Access Control
--------------

The module implements several security layers:

* Database-level access controls via ``ir.model.access.csv``
* Vault-level security via vault_connector
* UI-level restrictions based on user permissions
* Audit trails via chatter integration

Backup Considerations
---------------------

For complete backup coverage:

* **Odoo Database**: Contains public keys, relay configs, partner associations
* **Vault Storage**: Contains private keys (backup according to vault procedures)
* **Configuration**: Document custom relay configurations

.. important::
   Private keys in vault are not included in standard Odoo database backups.
   Ensure your vault backup strategy covers Nostr private keys.
