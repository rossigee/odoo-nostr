# -*- coding: utf-8 -*-

import requests
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class NostrRelay(models.Model):
    _name = "nostr.relay"
    _description = "Nostr Relay Management"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Relay Name",
        required=True,
        help="Descriptive name for this relay",
        tracking=True,
    )
    url = fields.Char(
        string="Relay URL",
        required=True,
        help="WebSocket URL of the Nostr relay (e.g., wss://relay.example.com)",
        tracking=True,
    )
    description = fields.Text(
        string="Description", help="Description of the relay and its purpose"
    )

    # Status and configuration
    is_active = fields.Boolean(
        string="Active",
        default=True,
        help="Whether this relay is currently active",
        tracking=True,
    )
    is_read = fields.Boolean(
        string="Read", default=True, help="Use this relay for reading events"
    )
    is_write = fields.Boolean(
        string="Write", default=True, help="Use this relay for publishing events"
    )

    # Connection details
    last_connected = fields.Datetime(string="Last Connected", readonly=True)
    connection_status = fields.Selection(
        [
            ("unknown", "Unknown"),
            ("connected", "Connected"),
            ("disconnected", "Disconnected"),
            ("error", "Error"),
        ],
        string="Status",
        default="unknown",
        readonly=True,
    )
    connection_error = fields.Text(string="Connection Error", readonly=True)

    # Relay information
    relay_info = fields.Text(
        string="Relay Info", readonly=True, help="NIP-11 relay information document"
    )
    supported_nips = fields.Char(
        string="Supported NIPs",
        readonly=True,
        help="Supported Nostr Implementation Possibilities",
    )
    software = fields.Char(
        string="Software", readonly=True, help="Relay software name and version"
    )
    contact = fields.Char(
        string="Contact", readonly=True, help="Relay operator contact information"
    )

    # Usage tracking
    event_count_read = fields.Integer(string="Events Read", default=0, readonly=True)
    event_count_write = fields.Integer(
        string="Events Written", default=0, readonly=True
    )

    # Notes and tracking
    notes = fields.Text(
        string="Notes", help="Additional notes about this relay", tracking=True
    )

    _sql_constraints = [
        ("unique_url", "UNIQUE(url)", "Relay URL must be unique."),
    ]

    @api.constrains("url")
    def _check_url_format(self):
        """Validate relay URL format"""
        for record in self:
            if record.url and not record.url.startswith(("ws://", "wss://")):
                raise ValidationError(
                    _("Relay URL must start with 'ws://' or 'wss://'")
                )

    def action_test_connection(self):
        """Test connection to the relay"""
        self.ensure_one()
        try:
            # For now, we'll just test if the HTTP version responds
            # In production, you'd want to test actual WebSocket connection
            http_url = self.url.replace("wss://", "https://").replace(
                "ws://", "http://"
            )

            response = requests.get(
                http_url, timeout=10, headers={"Accept": "application/nostr+json"}
            )

            if response.status_code == 200:
                self.write(
                    {
                        "connection_status": "connected",
                        "last_connected": fields.Datetime.now(),
                        "connection_error": False,
                    }
                )

                # Try to parse NIP-11 relay information
                try:
                    relay_info = response.json()
                    self.write(
                        {
                            "relay_info": str(relay_info),
                            "supported_nips": ",".join(
                                map(str, relay_info.get("supported_nips", []))
                            ),
                            "software": relay_info.get("software", ""),
                            "contact": relay_info.get("contact", ""),
                        }
                    )
                except Exception:
                    pass  # Not all relays support NIP-11

                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Connection Successful"),
                        "message": _("Successfully connected to relay"),
                        "type": "success",
                    },
                }
            else:
                raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            self.write(
                {
                    "connection_status": "error",
                    "connection_error": str(e),
                }
            )
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Connection Failed"),
                    "message": str(e),
                    "type": "danger",
                },
            }

    def increment_read_count(self):
        """Increment read event counter"""
        self.event_count_read += 1

    def increment_write_count(self):
        """Increment write event counter"""
        self.event_count_write += 1
