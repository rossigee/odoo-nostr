# -*- coding: utf-8 -*-

import hashlib
import logging
import secrets
import uuid

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# Bech32 implementation for Nostr keys
BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def bech32_polymod(values):
    """Internal function for bech32 checksum"""
    generator = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk


def bech32_hrp_expand(hrp):
    """Expand the HRP into values for checksum computation"""
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def bech32_verify_checksum(hrp, data):
    """Verify a checksum given HRP and converted data characters"""
    return bech32_polymod(bech32_hrp_expand(hrp) + data) == 1


def bech32_create_checksum(hrp, data):
    """Compute the checksum values given HRP and data"""
    values = bech32_hrp_expand(hrp) + data
    polymod = bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def bech32_encode(hrp, data):
    """Encode a segwit address"""
    combined = data + bech32_create_checksum(hrp, data)
    return hrp + "1" + "".join([BECH32_CHARSET[d] for d in combined])


def bech32_decode(bech):
    """Decode a bech32 string, returning (hrp, data) or (None, None)"""
    if (any(ord(x) < 33 or ord(x) > 126 for x in bech)) or (
        bech.lower() != bech and bech.upper() != bech
    ):
        return (None, None)
    bech = bech.lower()
    pos = bech.rfind("1")
    if pos < 1 or pos + 7 > len(bech) or pos + 1 + 6 > len(bech):
        return (None, None)
    if not all(x in BECH32_CHARSET for x in bech[pos + 1 :]):
        return (None, None)
    hrp = bech[:pos]
    data = [BECH32_CHARSET.find(x) for x in bech[pos + 1 :]]
    if not bech32_verify_checksum(hrp, data):
        return (None, None)
    return (hrp, data[:-6])


def convertbits(data, frombits, tobits, pad=True):
    """General power-of-2 base conversion"""
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            return None
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None
    return ret


class NostrKey(models.Model):
    _name = "nostr.key"
    _description = "Nostr Key Management"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Name",
        required=True,
        help="Descriptive name for this key pair",
        tracking=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Partner associated with this Nostr key (optional)",
        tracking=True,
    )
    key_type = fields.Selection(
        [("generated", "Generated"), ("imported", "Imported")],
        string="Key Type",
        default="generated",
        help="Whether key was generated or imported",
    )

    # Fields for importing existing keys
    import_nsec = fields.Char(
        string="Import Private Key (nsec)",
        help="Paste existing nsec private key to import",
    )
    import_npub = fields.Char(
        string="Import Public Key (npub)",
        help="Paste existing npub public key to import",
    )

    # Temporary field to show generated private key once
    generated_private_key = fields.Char(
        string="Generated Private Key",
        help="Private key shown only once during generation",
    )

    public_key = fields.Char(
        string="Public Key (npub)",
        readonly=True,
        help="Nostr public key in npub format",
    )
    public_key_hex = fields.Char(
        string="Public Key (hex)",
        readonly=True,
        help="Nostr public key in hexadecimal format",
    )
    vault_key_id = fields.Char(
        string="Vault Key ID",
        readonly=True,
        help="Reference ID for the private key stored in vault",
    )
    created_date = fields.Datetime(
        string="Created Date", default=fields.Datetime.now, readonly=True
    )
    notes = fields.Text(
        string="Notes", help="Additional notes about this key pair", tracking=True
    )
    has_private_key = fields.Boolean(
        string="Has Private Key", compute="_compute_has_private_key", store=True
    )

    _sql_constraints = [
        ("unique_public_key", "UNIQUE(public_key)", "Public key must be unique."),
    ]

    @api.depends("vault_key_id")
    def _compute_has_private_key(self):
        """Compute whether this key has a private key stored"""
        for record in self:
            record.has_private_key = bool(record.vault_key_id)

    @api.model
    def create(self, vals):
        """Override create to auto-generate or import keys"""
        # If this is a new record without keys, generate them
        if (
            not vals.get("public_key")
            and not vals.get("import_nsec")
            and not vals.get("import_npub")
        ):
            # Auto-generate key pair
            return self.generate_key_pair(vals.get("partner_id"), vals.get("name"))
        elif vals.get("import_nsec") or vals.get("import_npub"):
            # Import existing keys
            return self._import_key_pair(vals)
        else:
            # Standard creation (for internal use)
            return super().create(vals)

    def write(self, vals):
        """Override write to clear generated private key after save"""
        result = super().write(vals)
        # Clear generated private key field to ensure it's not permanently stored
        for record in self:
            if record.generated_private_key and not self.env.context.get(
                "keep_generated_key"
            ):
                record.with_context(keep_generated_key=True).write(
                    {"generated_private_key": False}
                )
        return result

    def _import_key_pair(self, vals):
        """Import existing nsec/npub key pair"""
        import_nsec = vals.get("import_nsec") or ""
        import_npub = vals.get("import_npub") or ""

        # Handle cases where fields come as False/None
        if not isinstance(import_nsec, str):
            import_nsec = ""
        if not isinstance(import_npub, str):
            import_npub = ""

        import_nsec = import_nsec.strip()
        import_npub = import_npub.strip()

        if import_nsec:
            # Import from nsec (private key)
            private_key_hex = self._nsec_to_hex(import_nsec)
            public_key_hex = self._derive_public_key(private_key_hex)
            public_key_npub = self._hex_to_npub(public_key_hex)

            # Store private key in vault
            vault_key_id = self._store_private_key_in_vault(
                private_key_hex, vals.get("partner_id"), vals.get("name")
            )

            # Create record - show imported private key once
            create_vals = {
                "name": vals.get("name"),
                "partner_id": vals.get("partner_id"),
                "key_type": "imported",
                "public_key": public_key_npub,
                "public_key_hex": public_key_hex,
                "vault_key_id": vault_key_id,
                "generated_private_key": import_nsec,  # Show once after key generation
            }

        elif import_npub:
            # Import from npub (public key only)
            public_key_hex = self._npub_to_hex(import_npub)

            create_vals = {
                "name": vals.get("name"),
                "partner_id": vals.get("partner_id"),
                "key_type": "imported",
                "public_key": import_npub,
                "public_key_hex": public_key_hex,
                "vault_key_id": False,  # No private key
            }
        else:
            raise ValidationError(
                _(
                    "Either nsec (private key) or npub (public key) must be provided for import"
                )
            )

        return super().create(create_vals)

    @api.model
    def generate_key_pair(self, partner_id, name):
        """Generate a new Nostr key pair and store private key in vault"""
        # Generate 32 random bytes for private key
        private_key_bytes = secrets.token_bytes(32)
        private_key_hex = private_key_bytes.hex()

        # Derive public key from private key (secp256k1)
        # Note: This is a simplified implementation - you'd need a proper secp256k1 library
        public_key_hex = self._derive_public_key(private_key_hex)
        public_key_npub = self._hex_to_npub(public_key_hex)

        # Store private key in vault
        vault_key_id = self._store_private_key_in_vault(
            private_key_hex, partner_id, name
        )

        # Convert private key to nsec format for one-time display
        private_key_nsec = self._hex_to_nsec(private_key_hex)

        # Create the record with temporary private key display
        return self.create(
            {
                "name": name,
                "partner_id": partner_id,
                "public_key": public_key_npub,
                "public_key_hex": public_key_hex,
                "vault_key_id": vault_key_id,
                "generated_private_key": private_key_nsec,
            }
        )

    def _derive_public_key(self, private_key_hex):
        """Derive public key from private key using secp256k1"""
        try:
            # Try to use secp256k1 library if available
            import secp256k1

            private_key_bytes = bytes.fromhex(private_key_hex)
            privkey = secp256k1.PrivateKey(private_key_bytes)
            pubkey = privkey.pubkey.serialize(compressed=True)
            # Remove the compression prefix (0x02 or 0x03) to get the x-coordinate
            return pubkey[1:].hex()
        except ImportError:
            try:
                # Fallback to coincurve library (Windows-compatible alternative)
                from coincurve import PrivateKey

                private_key_bytes = bytes.fromhex(private_key_hex)
                privkey = PrivateKey(private_key_bytes)
                pubkey = privkey.public_key.format(compressed=True)
                # Remove the compression prefix (0x02 or 0x03) to get the x-coordinate
                return pubkey[1:].hex()
            except ImportError:
                _logger.error(
                    "Neither secp256k1 nor coincurve library available - install one for proper cryptography"
                )
                # Fallback to simple hash (for development only - NOT SECURE)
                return hashlib.sha256(private_key_hex.encode()).hexdigest()[:64]

    def _hex_to_npub(self, public_key_hex):
        """Convert hex public key to npub format"""
        # Convert hex to bytes
        pubkey_bytes = bytes.fromhex(public_key_hex)
        # Convert to 5-bit groups for bech32
        converted = convertbits(pubkey_bytes, 8, 5)
        if converted is None:
            raise ValueError("Invalid public key for bech32 encoding")
        # Encode with 'npub' prefix
        return bech32_encode("npub", converted)

    def _store_private_key_in_vault(self, private_key_hex, partner_id, name):
        """Store private key in vault and return vault key ID"""
        vault_connector = self.env["vault.connector"]

        # Generate UUID for vault key ID
        vault_key_id = str(uuid.uuid4())

        # Check vault status first
        status = vault_connector.check_vault_status()
        if not status.get("accessible"):
            raise ValidationError(
                _(f"Vault is not accessible: {status.get('error', 'Unknown error')}")
            )

        # Store in vault using correct API with UUID
        vault_connector.set_secret(
            vault_key_id,
            {
                "private_key": private_key_hex,
                "partner_id": partner_id,
                "key_name": name,
                "description": f"Nostr private key for {name} (Partner ID: {partner_id})",
                "created_date": fields.Datetime.now().isoformat(),
            },
        )
        return vault_key_id

    def _nsec_to_hex(self, nsec):
        """Convert nsec format to hex private key"""
        # Decode bech32
        hrp, data = bech32_decode(nsec)
        if hrp != "nsec" or data is None:
            raise ValueError("Invalid nsec format")
        # Convert from 5-bit to 8-bit
        decoded = convertbits(data, 5, 8, False)
        if decoded is None or len(decoded) != 32:
            raise ValueError("Invalid nsec data length")
        # Convert to hex
        return bytes(decoded).hex()

    def _npub_to_hex(self, npub):
        """Convert npub format to hex public key"""
        # Decode bech32
        hrp, data = bech32_decode(npub)
        if hrp != "npub" or data is None:
            raise ValueError("Invalid npub format")
        # Convert from 5-bit to 8-bit
        decoded = convertbits(data, 5, 8, False)
        if decoded is None or len(decoded) != 32:
            raise ValueError("Invalid npub data length")
        # Convert to hex
        return bytes(decoded).hex()

    def _hex_to_nsec(self, private_key_hex):
        """Convert hex private key to nsec format"""
        # Convert hex to bytes
        privkey_bytes = bytes.fromhex(private_key_hex)
        if len(privkey_bytes) != 32:
            raise ValueError("Private key must be 32 bytes")
        # Convert to 5-bit groups for bech32
        converted = convertbits(privkey_bytes, 8, 5)
        if converted is None:
            raise ValueError("Invalid private key for bech32 encoding")
        # Encode with 'nsec' prefix
        return bech32_encode("nsec", converted)
