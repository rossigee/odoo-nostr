# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class NostrKeyImportWizard(models.TransientModel):
    _name = "nostr.key.import.wizard"
    _description = "Nostr Key Import Wizard"

    # Step 1 fields
    name = fields.Char(
        string="Key Name", required=True, help="Descriptive name for this key pair"
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Partner associated with this Nostr key (optional)",
    )

    # Import fields
    import_nsec = fields.Char(
        string="Private Key (nsec)",
        help="Import existing nsec private key (will derive npub automatically)",
    )
    import_npub = fields.Char(
        string="Public Key (npub)",
        help="Import existing npub public key (read-only contact)",
    )

    # Step 2 fields (import results)
    imported_nsec = fields.Char(
        string="Imported Private Key (nsec)",
        readonly=True,
        help="Imported private key - confirmed for secure storage",
    )
    imported_npub = fields.Char(
        string="Imported Public Key (npub)",
        readonly=True,
        help="Public key (imported or derived from nsec)",
    )
    import_type = fields.Selection(
        [("nsec", "Private Key Import"), ("npub", "Public Key Only")],
        string="Import Type",
        readonly=True,
    )

    # Wizard state
    step = fields.Selection(
        [("step1", "Import Details"), ("step2", "Confirm Import")],
        default="step1",
        string="Step",
    )

    @api.constrains("import_nsec", "import_npub")
    def _check_import_fields(self):
        """Ensure exactly one import field is provided"""
        for record in self:
            if record.step == "step1":
                nsec_provided = bool(record.import_nsec and record.import_nsec.strip())
                npub_provided = bool(record.import_npub and record.import_npub.strip())

                if not nsec_provided and not npub_provided:
                    raise ValidationError(
                        _(
                            "Please provide either an nsec (private key) or npub (public key) to import."
                        )
                    )
                if nsec_provided and npub_provided:
                    raise ValidationError(
                        _(
                            "Please provide only one key format - either nsec OR npub, not both."
                        )
                    )

    def action_validate_import(self):
        """Validate the import data and move to step 2"""
        self.ensure_one()

        nsec = (self.import_nsec or "").strip()
        npub = (self.import_npub or "").strip()

        if nsec:
            # Import from nsec (private key)
            try:
                # Validate nsec format by attempting conversion
                nostr_key_model = self.env["nostr.key"]
                private_key_hex = nostr_key_model._nsec_to_hex(nsec)
                public_key_hex = nostr_key_model._derive_public_key(private_key_hex)
                derived_npub = nostr_key_model._hex_to_npub(public_key_hex)

                self.write(
                    {
                        "step": "step2",
                        "import_type": "nsec",
                        "imported_nsec": nsec,
                        "imported_npub": derived_npub,
                    }
                )
            except Exception as e:
                raise ValidationError(_("Invalid nsec format: {}").format(str(e)))

        elif npub:
            # Import from npub (public key only)
            try:
                # Validate npub format by attempting conversion
                nostr_key_model = self.env["nostr.key"]
                public_key_hex = nostr_key_model._npub_to_hex(npub)

                self.write(
                    {
                        "step": "step2",
                        "import_type": "npub",
                        "imported_nsec": False,
                        "imported_npub": npub,
                    }
                )
            except Exception as e:
                raise ValidationError(_("Invalid npub format: {}").format(str(e)))

        return {
            "type": "ir.actions.act_window",
            "name": "Import Nostr Key",
            "res_model": "nostr.key.import.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_import_key(self):
        """Import the key and finish wizard"""
        self.ensure_one()

        # Create the key using the import method
        vals = {
            "name": self.name,
            "partner_id": self.partner_id.id if self.partner_id else False,
            "import_nsec": self.imported_nsec if self.import_type == "nsec" else False,
            "import_npub": self.imported_npub if self.import_type == "npub" else False,
        }

        created_key = self.env["nostr.key"]._import_key_pair(vals)

        return {
            "type": "ir.actions.act_window",
            "name": "Nostr Key",
            "res_model": "nostr.key",
            "res_id": created_key.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_back(self):
        """Go back to step 1"""
        self.ensure_one()
        self.write({"step": "step1"})

        return {
            "type": "ir.actions.act_window",
            "name": "Import Nostr Key",
            "res_model": "nostr.key.import.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
