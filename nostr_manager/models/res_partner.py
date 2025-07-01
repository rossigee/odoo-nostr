# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    nostr_key_ids = fields.One2many(
        "nostr.key",
        "partner_id",
        string="Nostr Keys",
        help="Nostr key pairs associated with this partner",
    )
    nostr_key_count = fields.Integer(
        string="Nostr Key Count", compute="_compute_nostr_key_count"
    )
    active_nostr_key_id = fields.Many2one(
        "nostr.key",
        string="Active Nostr Key",
        domain="[('partner_id', '=', id)]",
        help="Primary Nostr key for this partner",
    )

    @api.depends("nostr_key_ids")
    def _compute_nostr_key_count(self):
        """Compute the count of Nostr keys for this partner"""
        for partner in self:
            partner.nostr_key_count = len(partner.nostr_key_ids)

    def action_view_nostr_keys(self):
        """Open the list of Nostr keys for this partner"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"Nostr Keys - {self.name}",
            "res_model": "nostr.key",
            "view_mode": "tree,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }

    def generate_nostr_key(self, key_name=None):
        """Generate a new Nostr key pair for this partner"""
        self.ensure_one()
        if not key_name:
            key_name = f"Default Key {fields.Datetime.now().strftime('%Y-%m-%d')}"

        nostr_key = self.env["nostr.key"].generate_key_pair(self.id, key_name)

        # Set as active key if this is the first key for the partner
        if not self.active_nostr_key_id:
            self.active_nostr_key_id = nostr_key

        return nostr_key
