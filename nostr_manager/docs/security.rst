=================
Security Overview
=================

The Nostr Manager module implements multiple layers of security to protect Nostr private keys and ensure safe operations.

Key Format Overview
===================

Before discussing security, it's important to understand Nostr key formats:

**nsec (Private Key)**
  * Format: ``nsec1...`` (63 characters)
  * Contains your secret signing key
  * Used to prove identity and sign messages
  * Must be kept absolutely secret

**npub (Public Key)**
  * Format: ``npub1...`` (63 characters)
  * Your public Nostr identity/address
  * Derived from nsec using secp256k1 cryptography
  * Safe to share publicly

.. important::
   The relationship is one-way: nsec → npub is possible, but npub → nsec is cryptographically impossible.

Private Key Security
====================

Vault Storage
-------------

Private keys are **never** stored in the Odoo database. Instead:

* Private keys are stored in HashiCorp Vault using the ``vault_connector`` module
* Each private key gets a unique UUID reference stored in the database
* The actual private key material is only accessible through vault operations

One-Time Display
----------------

For maximum security, private keys are shown only once:

* During key generation in the 2-step wizard
* Immediately after importing an existing key
* Never displayed again through the application interface

.. warning::
   Users must copy and save private keys during the one-time display.
   The application cannot recover private keys after this point.

Key Generation Security
=======================

Cryptographic Randomness
------------------------

Key generation uses Python's ``secrets`` module:

.. code-block:: python

   import secrets
   private_key_bytes = secrets.token_bytes(32)

This provides cryptographically secure random number generation suitable for key material.

Secure Transmission
-------------------

* Private keys are transmitted directly to vault without intermediate storage
* No private key material is logged or cached
* Memory containing private keys is not persisted to disk

Access Control
==============

Database Permissions
--------------------

The module implements role-based access control:

**Regular Users (base.group_user)**
  * Create, read, update keys and relays
  * Cannot delete records
  * Cannot view vault key IDs

**System Administrators (base.group_system)**
  * Full CRUD operations
  * Can view vault key IDs for debugging
  * Can delete keys from system (vault storage remains)

Vault Permissions
-----------------

Vault access is controlled by the ``vault_connector`` module:

* Separate authentication tokens for vault access
* Per-path permissions in vault
* Audit logging at vault level

UI Security
-----------

Form-level security prevents unauthorized access:

* Copy buttons use secure JavaScript clipboard API
* Private key fields are never editable after creation
* Vault operations require proper authentication

Audit and Compliance
=====================

Activity Tracking
-----------------

All key operations are tracked via Odoo's chatter system:

* Key creation and naming changes
* Partner associations
* Notes and documentation updates
* File attachments (QR codes, backups)

What's NOT Tracked
~~~~~~~~~~~~~~~~~~

For security reasons, the following are not logged:

* Private key material
* Vault access operations (logged separately in vault)
* Key usage for signing (outside scope of this module)

Vault Audit Trail
-----------------

HashiCorp Vault provides its own audit logging:

* All secret access operations
* Authentication attempts
* Policy violations
* Administrative operations

Security Best Practices
========================

For Administrators
------------------

**Vault Security**
  * Use proper vault authentication (not root tokens in production)
  * Implement vault policies for least-privilege access
  * Regular vault backup and disaster recovery testing
  * Monitor vault audit logs

**Odoo Security**
  * Limit system administrator access
  * Regular database backups (excludes private keys)
  * Monitor user access patterns
  * Keep modules updated

For End Users
-------------

**Private Key Management**
  * Save private keys in secure offline storage immediately
  * Use hardware security modules for high-value keys
  * Never share private keys via email or chat
  * Generate separate keys for different purposes

**Operational Security**
  * Use strong Odoo user passwords
  * Log out of shared computers
  * Report suspected security incidents
  * Verify public key authenticity through multiple channels

Threat Model
============

Protected Against
-----------------

* **Database Compromise**: Private keys not in database
* **Application Compromise**: Keys stored in separate vault system
* **Insider Threats**: Access controls and audit trails
* **Accidental Exposure**: One-time display and secure storage

Limitations
-----------

* **Vault Compromise**: If vault is compromised, private keys are at risk
* **Memory Attacks**: Private keys temporarily in application memory during operations
* **Social Engineering**: Users may be tricked into revealing private keys
* **Endpoint Compromise**: Malware on user devices could intercept private keys during display

Security Considerations for Development
=======================================

Cryptographic Implementation
----------------------------

The module uses industry-standard cryptographic libraries:

* **secp256k1** for elliptic curve operations (key derivation, signing)
* **Built-in bech32** implementation for address encoding (nsec/npub formats)
* Fallback error handling for missing dependencies

Code Security
-------------

* Input validation on all user-provided data
* Parameterized queries to prevent SQL injection
* Proper error handling without information leakage
* Regular security code reviews

Incident Response
=================

Suspected Key Compromise
-----------------------

If a private key may be compromised:

1. **Immediate Actions**
   * Generate new key pair for affected partner
   * Update partner's active key to new key
   * Notify affected parties to update their records

2. **Investigation**
   * Review audit logs for unauthorized access
   * Check vault logs for unusual activity
   * Interview affected users

3. **Recovery**
   * Revoke compromised key if possible (protocol-dependent)
   * Update all systems using the compromised key
   * Document incident and lessons learned

Vault Security Incident
-----------------------

If vault security is compromised:

1. **Emergency Response**
   * Immediately revoke vault access tokens
   * Isolate vault from network if necessary
   * Assess scope of potential key exposure

2. **Recovery Planning**
   * Plan new vault deployment
   * Generate new keys for all critical partners
   * Coordinate with affected business partners

3. **System Restoration**
   * Deploy new vault with enhanced security
   * Migrate to new key pairs
   * Update all integration points
