# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class NostrKeyGeneratorWizard(models.TransientModel):
    _name = "nostr.key.generator.wizard"
    _description = "Nostr Key Generation Wizard"

    # Step 1 fields
    name = fields.Char(
        string="Key Name", required=True, help="Descriptive name for this key pair"
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Partner associated with this Nostr key (optional)",
    )

    # Step 2 fields (generated results)
    generated_nsec = fields.Char(
        string="Private Key (nsec)",
        readonly=True,
        help="Generated private key - save this securely!",
    )
    generated_npub = fields.Char(
        string="Public Key (npub)",
        readonly=True,
        help="Generated public key for sharing",
    )

    # Wizard state
    step = fields.Selection(
        [("step1", "Key Details"), ("step2", "Generated Keys")],
        default="step1",
        string="Step",
    )

    def action_generate_keys(self):
        """Generate the key pair and move to step 2"""
        self.ensure_one()

        # Generate the key pair using the main model method
        nostr_key = self.env["nostr.key"].generate_key_pair(
            self.partner_id.id if self.partner_id else False, self.name
        )

        # Get the generated private key from vault for display
        vault_connector = self.env["vault.connector"]
        status = vault_connector.check_vault_status()
        if not status.get("accessible"):
            raise ValidationError(
                _("Vault is not accessible: {}").format(
                    status.get("error", "Unknown error")
                )
            )

        secret_data = vault_connector.get_secret(nostr_key.vault_key_id)
        if not secret_data or "private_key" not in secret_data:
            raise ValidationError(
                _("Failed to retrieve generated private key from vault")
            )

        private_key_hex = secret_data["private_key"]
        private_key_nsec = nostr_key._hex_to_nsec(private_key_hex)

        # Update wizard with generated keys
        self.write(
            {
                "step": "step2",
                "generated_nsec": private_key_nsec,
                "generated_npub": nostr_key.public_key,
            }
        )

        return {
            "type": "ir.actions.act_window",
            "name": "Generate Nostr Key",
            "res_model": "nostr.key.generator.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": {"created_key_id": nostr_key.id},
        }

    def action_finish(self):
        """Finish wizard and open the created key"""
        self.ensure_one()
        created_key_id = self.env.context.get("created_key_id")

        if created_key_id:
            return {
                "type": "ir.actions.act_window",
                "name": "Nostr Key",
                "res_model": "nostr.key",
                "res_id": created_key_id,
                "view_mode": "form",
                "target": "current",
            }
        else:
            return {"type": "ir.actions.act_window_close"}

    def action_back(self):
        """Go back to step 1"""
        self.ensure_one()
        self.write({"step": "step1"})

        return {
            "type": "ir.actions.act_window",
            "name": "Generate Nostr Key",
            "res_model": "nostr.key.generator.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
