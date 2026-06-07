# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestNostrWizards(TransactionCase):
    """Test Nostr key generation and import wizards"""

    def setUp(self):
        super().setUp()
        self.generator_wizard_model = self.env["nostr.key.generator.wizard"]
        self.import_wizard_model = self.env["nostr.key.import.wizard"]
        self.nostr_key_model = self.env["nostr.key"]
        self.partner = self.env["res.partner"].create(
            {"name": "Wizard Test Partner", "email": "wizard@test.com"}
        )

    @patch(
        "odoo.addons.nostr_manager.models.nostr_key.NostrKey._store_private_key_in_vault"
    )
    @patch(
        "odoo.addons.vault_connector.models.vault_connector.VaultConnector.check_vault_status"
    )
    @patch(
        "odoo.addons.vault_connector.models.vault_connector.VaultConnector.get_secret"
    )
    def test_generator_wizard_flow(
        self, mock_get_secret, mock_vault_status, mock_store_vault
    ):
        """Test the complete generator wizard flow"""
        # Mock vault operations
        mock_vault_status.return_value = {"accessible": True}
        mock_store_vault.return_value = "wizard-gen-uuid"
        mock_get_secret.return_value = {"private_key": "0123456789abcdef" * 4}

        # Step 1: Create wizard with initial data
        wizard = self.generator_wizard_model.create(
            {
                "name": "Wizard Generated Key",
                "partner_id": self.partner.id,
                "step": "step1",
            }
        )

        self.assertEqual(wizard.step, "step1")
        self.assertEqual(wizard.name, "Wizard Generated Key")
        self.assertEqual(wizard.partner_id, self.partner)

        # Step 2: Generate keys
        result = wizard.action_generate_keys()

        # Should move to step 2 and show generated keys
        wizard.invalidate_cache()
        self.assertEqual(wizard.step, "step2")
        self.assertTrue(wizard.generated_nsec)
        self.assertTrue(wizard.generated_npub)
        self.assertTrue(wizard.generated_nsec.startswith("nsec1"))
        self.assertTrue(wizard.generated_npub.startswith("npub1"))

        # Should return proper action
        self.assertEqual(result["res_model"], "nostr.key.generator.wizard")
        self.assertEqual(result["res_id"], wizard.id)
        self.assertIn("created_key_id", result["context"])

    def test_generator_wizard_back_action(self):
        """Test going back from step 2 to step 1"""
        wizard = self.generator_wizard_model.create(
            {"name": "Test Back Action", "step": "step2"}
        )

        result = wizard.action_back()

        wizard.invalidate_cache()
        self.assertEqual(wizard.step, "step1")
        self.assertEqual(result["res_model"], "nostr.key.generator.wizard")

    def test_generator_wizard_finish_action(self):
        """Test finishing the wizard and opening created key"""
        wizard = self.generator_wizard_model.create(
            {"name": "Test Finish", "step": "step2"}
        )

        # Mock context with created key
        created_key_id = 123
        wizard = wizard.with_context(created_key_id=created_key_id)

        result = wizard.action_finish()

        self.assertEqual(result["res_model"], "nostr.key")
        self.assertEqual(result["res_id"], created_key_id)
        self.assertEqual(result["target"], "current")

    def test_import_wizard_nsec_validation(self):
        """Test import wizard nsec validation"""
        # Generate valid nsec using known test hex
        test_hex = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        valid_nsec = self.nostr_key_model._hex_to_nsec(test_hex)
        
        # Valid nsec import
        wizard = self.import_wizard_model.create(
            {
                "name": "Import Test",
                "partner_id": self.partner.id,
                "import_nsec": valid_nsec,
                "import_npub": "",
                "step": "step1",
            }
        )

        # Should validate successfully
        result = wizard.action_validate_import()

        wizard.invalidate_cache()
        self.assertEqual(wizard.step, "step2")
        self.assertEqual(wizard.import_type, "nsec")
        self.assertTrue(wizard.imported_nsec)
        self.assertTrue(wizard.imported_npub)

    def test_import_wizard_npub_validation(self):
        """Test import wizard npub validation"""
        # Valid npub import
        wizard = self.import_wizard_model.create(
            {
                "name": "Import Public Key",
                "import_nsec": "",
                "import_npub": "npub1g53xlk3h3lf4dqhzqchvl8rphk6nqcaxn49m5azmcqtftwamg36qqkvp6c",
                "step": "step1",
            }
        )

        wizard.action_validate_import()

        wizard.invalidate_cache()
        self.assertEqual(wizard.step, "step2")
        self.assertEqual(wizard.import_type, "npub")
        self.assertFalse(wizard.imported_nsec)
        self.assertTrue(wizard.imported_npub)

    def test_import_wizard_validation_errors(self):
        """Test import wizard validation error handling"""
        # Test invalid nsec format
        wizard = self.import_wizard_model.create(
            {
                "name": "Invalid Import",
                "import_nsec": "invalid_nsec_format",
                "step": "step1",
            }
        )

        with self.assertRaises(ValidationError):
            wizard.action_validate_import()

        # Test invalid npub format
        wizard2 = self.import_wizard_model.create(
            {
                "name": "Invalid Import 2",
                "import_npub": "invalid_npub_format",
                "step": "step1",
            }
        )

        with self.assertRaises(ValidationError):
            wizard2.action_validate_import()

    def test_import_wizard_constraint_validation(self):
        """Test import wizard field constraints"""
        # Test providing both nsec and npub - should fail
        with self.assertRaises(ValidationError):
            self.import_wizard_model.create(
                {
                    "name": "Both Keys",
                    "import_nsec": "nsec1qy35v6y8x4lkmqy35v6y8x4lkmqy35v6y8x4lkmqy35v6y8x4lkmq0ecds5",
                    "import_npub": "npub1g53xlk3h3lf4dqhzqchvl8rphk6nqcaxn49m5azmcqtftwamg36qqkvp6c",
                    "step": "step1",
                }
            )

        # Test providing neither - should fail
        with self.assertRaises(ValidationError):
            self.import_wizard_model.create(
                {
                    "name": "No Keys",
                    "import_nsec": "",
                    "import_npub": "",
                    "step": "step1",
                }
            )

    @patch(
        "odoo.addons.nostr_manager.models.nostr_key.NostrKey._store_private_key_in_vault"
    )
    def test_import_wizard_nsec_import_action(self, mock_vault_store):
        """Test importing nsec through wizard"""
        mock_vault_store.return_value = "imported-uuid"

        # Generate valid nsec/npub pair
        test_hex = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        valid_nsec = self.nostr_key_model._hex_to_nsec(test_hex)
        public_hex = self.nostr_key_model._derive_public_key(test_hex)
        valid_npub = self.nostr_key_model._hex_to_npub(public_hex)

        # Create wizard in step 2 (already validated)
        wizard = self.import_wizard_model.create(
            {
                "name": "Import Private Key",
                "partner_id": self.partner.id,
                "import_type": "nsec",
                "imported_nsec": valid_nsec,
                "imported_npub": valid_npub,
                "step": "step2",
            }
        )

        result = wizard.action_import_key()

        # Should create key and return action to view it
        self.assertEqual(result["res_model"], "nostr.key")
        self.assertEqual(result["target"], "current")
        self.assertIn("res_id", result)

        # Verify key was created with correct properties
        created_key = self.env["nostr.key"].browse(result["res_id"])
        self.assertEqual(created_key.name, "Import Private Key")
        self.assertEqual(created_key.partner_id, self.partner)
        self.assertEqual(created_key.key_type, "imported")
        self.assertTrue(created_key.has_private_key)

    def test_import_wizard_npub_import_action(self):
        """Test importing npub through wizard"""
        # Create wizard in step 2 (already validated)
        wizard = self.import_wizard_model.create(
            {
                "name": "Import Public Key",
                "import_type": "npub",
                "imported_nsec": False,
                "imported_npub": "npub1g53xlk3h3lf4dqhzqchvl8rphk6nqcaxn49m5azmcqtftwamg36qqkvp6c",
                "step": "step2",
            }
        )

        result = wizard.action_import_key()

        # Verify key was created as public-only
        created_key = self.env["nostr.key"].browse(result["res_id"])
        self.assertEqual(created_key.name, "Import Public Key")
        self.assertEqual(created_key.key_type, "imported")
        self.assertFalse(created_key.has_private_key)

    def test_import_wizard_back_action(self):
        """Test going back in import wizard"""
        wizard = self.import_wizard_model.create({"name": "Test Back", "step": "step2"})

        result = wizard.action_back()

        wizard.invalidate_cache()
        self.assertEqual(wizard.step, "step1")
        self.assertEqual(result["res_model"], "nostr.key.import.wizard")

    @patch(
        "odoo.addons.vault_connector.models.vault_connector.VaultConnector.check_vault_status"
    )
    def test_generator_wizard_vault_error(self, mock_vault_status):
        """Test generator wizard handling vault errors"""
        # Mock vault as inaccessible
        mock_vault_status.return_value = {
            "accessible": False,
            "error": "Vault connection failed",
        }

        wizard = self.generator_wizard_model.create(
            {"name": "Vault Error Test", "step": "step1"}
        )

        with self.assertRaises(ValidationError) as cm:
            wizard.action_generate_keys()

        self.assertIn("Vault is not accessible", str(cm.exception))

    def test_wizard_step_transitions(self):
        """Test wizard step state management"""
        # Generator wizard
        gen_wizard = self.generator_wizard_model.create(
            {"name": "Step Test", "step": "step1"}
        )

        # Import wizard
        import_wizard = self.import_wizard_model.create(
            {"name": "Step Test", "step": "step1"}
        )

        # Both should start at step1
        self.assertEqual(gen_wizard.step, "step1")
        self.assertEqual(import_wizard.step, "step1")

        # Test field selections
        step_selection = gen_wizard._fields["step"].selection
        self.assertIn(("step1", "Key Details"), step_selection)
        self.assertIn(("step2", "Generated Keys"), step_selection)

        import_step_selection = import_wizard._fields["step"].selection
        self.assertIn(("step1", "Import Details"), import_step_selection)
        self.assertIn(("step2", "Confirm Import"), import_step_selection)
