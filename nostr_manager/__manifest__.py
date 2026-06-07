# -*- coding: utf-8 -*-
{
    "name": "Nostr Manager",
    "summary": """
        Comprehensive Nostr client with key management, relay management,
        and partner integration""",
    "description": """
        Complete Nostr management suite for Odoo:
        • Secure key generation and management with vault integration
        • Address book for collecting Nostr identities (npubs)
        • Relay management with 12+ default public relays
        • Partner integration for business use cases
        • Connection testing and NIP-11 relay information
        • Activity tracking and chatter integration

        External Dependencies:
        • secp256k1 or coincurve (for elliptic curve cryptography)
    """,
    "author": "Ross Golder",
    "website": "http://www.golder.org",
    "category": "Security",
    "version": "16.0.1.0.1",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "base",
        "mail",
        "vault_connector",
    ],
    # external python dependencies
    "external_dependencies": {
        "python": [
            "secp256k1"
        ],  # Primary dependency - fallback to coincurve if not available
    },
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "data/default_relays.xml",
        "views/nostr_key_generator_wizard_views.xml",
        "views/nostr_key_import_wizard_views.xml",
        "views/nostr_key_views.xml",
        "views/nostr_relay_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
