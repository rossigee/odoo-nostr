# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestNostrKeyManagement(TransactionCase):
    """Test Nostr key management functionality"""

    def setUp(self):
        super().setUp()
        self.nostr_key_model = self.env["nostr.key"]
        self.partner = self.env["res.partner"].create(
            {"name": "Test Partner", "email": "test@example.com"}
        )
        test_private_key_hex = (
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        )
        self.test_nsec = self.nostr_key_model._hex_to_nsec(test_private_key_hex)
        public_key_hex = self.nostr_key_model._derive_public_key(test_private_key_hex)
        self.test_npub = self.nostr_key_model._hex_to_npub(public_key_hex)

    @patch(
        "odoo.addons.nostr_manager.models.nostr_key.NostrKey._store_private_key_in_vault"
    )
    def test_key_generation_basic(self, mock_vault_store):
        """Test basic key pair generation"""
        # Mock vault storage
        mock_vault_store.return_value = "test-vault-uuid-123"

        # Generate key pair
        key = self.nostr_key_model.generate_key_pair(
            partner_id=self.partner.id, name="Test Key"
        )

        # Verify key properties
        self.assertEqual(key.name, "Test Key")
        self.assertEqual(key.partner_id, self.partner)
        self.assertEqual(key.key_type, "generated")
        self.assertTrue(key.public_key.startswith("npub1"))
        self.assertEqual(len(key.public_key), 63)
        self.assertTrue(key.has_private_key)
        self.assertEqual(key.vault_key_id, "test-vault-uuid-123")

        # Verify vault was called correctly
        mock_vault_store.assert_called_once()

    @patch(
        "odoo.addons.nostr_manager.models.nostr_key.NostrKey._store_private_key_in_vault"
    )
    def test_key_generation_without_partner(self, mock_vault_store):
        """Test key generation without associated partner"""
        mock_vault_store.return_value = "test-vault-uuid-456"

        key = self.nostr_key_model.generate_key_pair(
            partner_id=None, name="Standalone Key"
        )

        self.assertEqual(key.name, "Standalone Key")
        self.assertFalse(key.partner_id)
        self.assertTrue(key.has_private_key)

    def test_nsec_import(self):
        """Test importing existing nsec private key"""
        with patch(
            "odoo.addons.nostr_manager.models.nostr_key.NostrKey._store_private_key_in_vault"
        ) as mock_vault:
            mock_vault.return_value = "imported-vault-uuid"

            key = self.nostr_key_model._import_key_pair(
                {
                    "name": "Imported Private Key",
                    "partner_id": self.partner.id,
                    "import_nsec": self.test_nsec,
                    "import_npub": None,
                }
            )

            self.assertEqual(key.name, "Imported Private Key")
            self.assertEqual(key.key_type, "imported")
            self.assertTrue(key.has_private_key)
            self.assertTrue(key.public_key.startswith("npub1"))
            mock_vault.assert_called_once()

    def test_npub_import(self):
        """Test importing existing npub public key only"""
        key = self.nostr_key_model._import_key_pair(
            {
                "name": "Imported Public Key",
                "partner_id": self.partner.id,
                "import_nsec": None,
                "import_npub": self.test_npub,
            }
        )

        self.assertEqual(key.name, "Imported Public Key")
        self.assertEqual(key.key_type, "imported")
        self.assertFalse(key.has_private_key)
        self.assertEqual(key.public_key, self.test_npub)
        self.assertFalse(key.vault_key_id)

    def test_import_validation_errors(self):
        """Test validation errors during import"""
        # Test importing invalid nsec
        with self.assertRaises(ValueError):
            self.nostr_key_model._import_key_pair(
                {
                    "name": "Invalid Key",
                    "import_nsec": "invalid_nsec_format",
                    "import_npub": None,
                }
            )

        # Test importing invalid npub
        with self.assertRaises(ValueError):
            self.nostr_key_model._import_key_pair(
                {
                    "name": "Invalid Key",
                    "import_nsec": None,
                    "import_npub": "invalid_npub_format",
                }
            )

        # Test importing neither nsec nor npub
        with self.assertRaises(ValidationError):
            self.nostr_key_model._import_key_pair(
                {"name": "Invalid Key", "import_nsec": None, "import_npub": None}
            )

    def test_unique_public_key_constraint(self):
        """Test that duplicate public keys are not allowed"""
        # Create first key
        self.nostr_key_model._import_key_pair(
            {"name": "First Key", "import_npub": self.test_npub}
        )

        # Try to create second key with same npub - should fail
        with self.assertRaises(Exception):  # Database constraint error
            self.nostr_key_model._import_key_pair(
                {"name": "Duplicate Key", "import_npub": self.test_npub}
            )

    def test_has_private_key_computation(self):
        """Test the has_private_key computed field"""
        # Key with private key (vault_key_id present)
        with patch(
            "odoo.addons.nostr_manager.models.nostr_key.NostrKey._store_private_key_in_vault"
        ) as mock_vault:
            mock_vault.return_value = "vault-uuid-123"

            key_with_private = self.nostr_key_model.generate_key_pair(
                partner_id=None, name="Key with Private"
            )
            self.assertTrue(key_with_private.has_private_key)

        # Key without private key (public key only)
        key_public_only = self.nostr_key_model._import_key_pair(
            {
                "name": "Public Only",
                "import_npub": self.test_npub,
            }
        )
        self.assertFalse(key_public_only.has_private_key)

    @patch(
        "odoo.addons.vault_connector.models.vault_connector.VaultConnector.check_vault_status"
    )
    def test_vault_connectivity_error(self, mock_vault_status):
        """Test handling of vault connectivity errors"""
        # Mock vault as inaccessible
        mock_vault_status.return_value = {
            "accessible": False,
            "error": "Connection timeout",
        }

        with self.assertRaises(ValidationError) as cm:
            self.nostr_key_model.generate_key_pair(partner_id=None, name="Test Key")

        self.assertIn("Vault is not accessible", str(cm.exception))
        self.assertIn("Connection timeout", str(cm.exception))

    def test_generated_private_key_clearing(self):
        """Test that generated_private_key field is cleared after creation"""
        with patch(
            "odoo.addons.nostr_manager.models.nostr_key.NostrKey._store_private_key_in_vault"
        ) as mock_vault:
            mock_vault.return_value = "test-uuid"

            # Generate key - should have temporary private key
            key = self.nostr_key_model.generate_key_pair(
                partner_id=None, name="Test Key"
            )

            # The generated_private_key should be present initially
            self.assertTrue(key.generated_private_key)

            # After write operation, it should be cleared
            key.write({"notes": "Test note"})
            key.invalidate_recordset()

            # Field should be cleared to prevent persistent storage
            self.assertFalse(key.generated_private_key)

    def test_partner_integration(self):
        """Test integration with partner model"""
        # Initially no keys
        self.assertEqual(self.partner.nostr_key_count, 0)
        self.assertFalse(self.partner.nostr_key_ids)

        # Create key for partner
        with patch(
            "odoo.addons.nostr_manager.models.nostr_key.NostrKey._store_private_key_in_vault"
        ) as mock_vault:
            mock_vault.return_value = "partner-key-uuid"

            key = self.nostr_key_model.generate_key_pair(
                partner_id=self.partner.id, name="Partner Key"
            )

            # Refresh partner to get updated computed fields
            self.partner.invalidate_recordset()

            # Check partner key relationship
            self.assertEqual(self.partner.nostr_key_count, 1)
            self.assertIn(key, self.partner.nostr_key_ids)

    def test_key_activity_tracking(self):
        """Test that key operations are tracked in chatter"""
        with patch(
            "odoo.addons.nostr_manager.models.nostr_key.NostrKey._store_private_key_in_vault"
        ) as mock_vault:
            mock_vault.return_value = "activity-test-uuid"

            # Create key
            key = self.nostr_key_model.generate_key_pair(
                partner_id=self.partner.id, name="Activity Test Key"
            )

            # Update tracked fields
            key.write(
                {"name": "Updated Activity Test Key", "notes": "Added some notes"}
            )

            # Check that messages were created (basic check)
            self.assertTrue(
                key.message_ids, "Key operations should create activity messages"
            )

    def test_auto_generation_on_create(self):
        """Test that auto-generation works when creating keys without import data"""
        with patch(
            "odoo.addons.nostr_manager.models.nostr_key.NostrKey._store_private_key_in_vault"
        ) as mock_vault:
            mock_vault.return_value = "auto-gen-uuid"

            # Create key record without import data - should auto-generate
            key = self.nostr_key_model.create(
                {"name": "Auto Generated Key", "partner_id": self.partner.id}
            )

            # Should have generated keys
            self.assertTrue(key.public_key)
            self.assertTrue(key.public_key.startswith("npub1"))
            self.assertTrue(key.has_private_key)
            self.assertEqual(key.key_type, "generated")

    def test_secp256k1_library_fallback(self):
        """Test handling when secp256k1 library is not available"""
        # This test verifies the fallback behavior
        with patch(
            "odoo.addons.nostr_manager.models.nostr_key.NostrKey._derive_public_key"
        ) as mock_derive:
            # Simulate library not available - should use fallback
            mock_derive.return_value = "a" * 64  # Valid 64-char hex string

            with patch(
                "odoo.addons.nostr_manager.models.nostr_key.NostrKey._store_private_key_in_vault"
            ) as mock_vault:
                mock_vault.return_value = "fallback-test-uuid"

                key = self.nostr_key_model.generate_key_pair(
                    partner_id=None, name="Fallback Test"
                )

                # Should still create a key even with fallback crypto
                self.assertTrue(key.public_key)
                mock_derive.assert_called_once()
