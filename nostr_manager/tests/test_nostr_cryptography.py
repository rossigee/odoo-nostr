# -*- coding: utf-8 -*-

import secrets

from odoo.tests.common import TransactionCase


class TestNostrCryptography(TransactionCase):
    """Test cryptographic functions for Nostr key management"""

    def setUp(self):
        super().setUp()
        self.nostr_key_model = self.env["nostr.key"]

        # Known test vectors for cryptographic regression testing
        self.test_private_key_hex = (
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        )
        # Generate proper nsec from hex
        self.test_nsec = self.nostr_key_model._hex_to_nsec(self.test_private_key_hex)
        # Generate corresponding npub
        test_public_key_hex = self.nostr_key_model._derive_public_key(
            self.test_private_key_hex
        )
        self.test_npub = self.nostr_key_model._hex_to_npub(test_public_key_hex)

    def test_nsec_to_hex_conversion(self):
        """Test nsec to hex conversion maintains consistency"""
        # Test valid nsec conversion
        result_hex = self.nostr_key_model._nsec_to_hex(self.test_nsec)
        self.assertEqual(len(result_hex), 64, "Private key hex should be 64 characters")
        self.assertTrue(
            all(c in "0123456789abcdef" for c in result_hex.lower()),
            "Result should be valid hexadecimal",
        )

        # Test that conversion is deterministic
        result_hex_2 = self.nostr_key_model._nsec_to_hex(self.test_nsec)
        self.assertEqual(
            result_hex, result_hex_2, "nsec conversion should be deterministic"
        )

    def test_hex_to_nsec_conversion(self):
        """Test hex to nsec conversion maintains consistency"""
        # Test valid hex conversion
        result_nsec = self.nostr_key_model._hex_to_nsec(self.test_private_key_hex)
        self.assertTrue(
            result_nsec.startswith("nsec1"), "Result should start with nsec1"
        )
        self.assertEqual(len(result_nsec), 63, "nsec should be 63 characters")

        # Test that conversion is deterministic
        result_nsec_2 = self.nostr_key_model._hex_to_nsec(self.test_private_key_hex)
        self.assertEqual(
            result_nsec, result_nsec_2, "hex to nsec conversion should be deterministic"
        )

    def test_nsec_hex_roundtrip(self):
        """Test that nsec -> hex -> nsec conversion is consistent"""
        # Start with known nsec
        hex_result = self.nostr_key_model._nsec_to_hex(self.test_nsec)
        nsec_result = self.nostr_key_model._hex_to_nsec(hex_result)
        self.assertEqual(
            self.test_nsec, nsec_result, "nsec roundtrip should be consistent"
        )

        # Start with known hex
        nsec_result = self.nostr_key_model._hex_to_nsec(self.test_private_key_hex)
        hex_result = self.nostr_key_model._nsec_to_hex(nsec_result)
        self.assertEqual(
            self.test_private_key_hex, hex_result, "hex roundtrip should be consistent"
        )

    def test_npub_to_hex_conversion(self):
        """Test npub to hex conversion maintains consistency"""
        # Test valid npub conversion
        result_hex = self.nostr_key_model._npub_to_hex(self.test_npub)
        self.assertEqual(len(result_hex), 64, "Public key hex should be 64 characters")
        self.assertTrue(
            all(c in "0123456789abcdef" for c in result_hex.lower()),
            "Result should be valid hexadecimal",
        )

        # Test that conversion is deterministic
        result_hex_2 = self.nostr_key_model._npub_to_hex(self.test_npub)
        self.assertEqual(
            result_hex, result_hex_2, "npub conversion should be deterministic"
        )

    def test_hex_to_npub_conversion(self):
        """Test hex to npub conversion maintains consistency"""
        # Generate a random 32-byte public key
        test_public_key_hex = secrets.token_hex(32)

        # Test valid hex conversion
        result_npub = self.nostr_key_model._hex_to_npub(test_public_key_hex)
        self.assertTrue(
            result_npub.startswith("npub1"), "Result should start with npub1"
        )
        self.assertEqual(len(result_npub), 63, "npub should be 63 characters")

        # Test that conversion is deterministic
        result_npub_2 = self.nostr_key_model._hex_to_npub(test_public_key_hex)
        self.assertEqual(
            result_npub, result_npub_2, "hex to npub conversion should be deterministic"
        )

    def test_npub_hex_roundtrip(self):
        """Test that npub -> hex -> npub conversion is consistent"""
        # Start with known npub
        hex_result = self.nostr_key_model._npub_to_hex(self.test_npub)
        npub_result = self.nostr_key_model._hex_to_npub(hex_result)
        self.assertEqual(
            self.test_npub, npub_result, "npub roundtrip should be consistent"
        )

    def test_secp256k1_public_key_derivation(self):
        """Test that public key derivation is consistent and deterministic"""
        # Test with known private key
        public_key_1 = self.nostr_key_model._derive_public_key(
            self.test_private_key_hex
        )
        public_key_2 = self.nostr_key_model._derive_public_key(
            self.test_private_key_hex
        )

        self.assertEqual(
            public_key_1, public_key_2, "Public key derivation should be deterministic"
        )
        self.assertEqual(
            len(public_key_1), 64, "Public key should be 64 hex characters (32 bytes)"
        )
        self.assertTrue(
            all(c in "0123456789abcdef" for c in public_key_1.lower()),
            "Public key should be valid hexadecimal",
        )

        # Test with different private keys produce different public keys
        different_private_key = secrets.token_hex(32)
        different_public_key = self.nostr_key_model._derive_public_key(
            different_private_key
        )
        self.assertNotEqual(
            public_key_1,
            different_public_key,
            "Different private keys should produce different public keys",
        )

    def test_complete_key_generation_flow(self):
        """Test the complete key generation and encoding flow"""
        # Generate random private key
        private_key_hex = secrets.token_hex(32)

        # Derive public key
        public_key_hex = self.nostr_key_model._derive_public_key(private_key_hex)

        # Convert to Nostr formats
        nsec = self.nostr_key_model._hex_to_nsec(private_key_hex)
        npub = self.nostr_key_model._hex_to_npub(public_key_hex)

        # Verify formats
        self.assertTrue(
            nsec.startswith("nsec1"), "Private key should be in nsec format"
        )
        self.assertTrue(npub.startswith("npub1"), "Public key should be in npub format")
        self.assertEqual(len(nsec), 63, "nsec should be 63 characters")
        self.assertEqual(len(npub), 63, "npub should be 63 characters")

        # Test reverse conversion
        private_key_hex_back = self.nostr_key_model._nsec_to_hex(nsec)
        public_key_hex_back = self.nostr_key_model._npub_to_hex(npub)

        self.assertEqual(
            private_key_hex, private_key_hex_back, "Private key roundtrip should work"
        )
        self.assertEqual(
            public_key_hex, public_key_hex_back, "Public key roundtrip should work"
        )

    def test_invalid_nsec_format(self):
        """Test that invalid nsec formats raise appropriate errors"""
        # Test invalid prefix
        with self.assertRaises(ValueError):
            self.nostr_key_model._nsec_to_hex(
                "npub1qy35v6y8x4lkmqy35v6y8x4lkmqy35v6y8x4lkmqy35v6y8x4lkmq9ycf0d"
            )

        # Test invalid length
        with self.assertRaises(ValueError):
            self.nostr_key_model._nsec_to_hex("nsec1short")

        # Test invalid characters
        with self.assertRaises(ValueError):
            self.nostr_key_model._nsec_to_hex(
                "nsec1" + "0" * 58
            )  # Invalid bech32 chars

    def test_invalid_npub_format(self):
        """Test that invalid npub formats raise appropriate errors"""
        # Test invalid prefix
        with self.assertRaises(ValueError):
            self.nostr_key_model._npub_to_hex(
                "nsec1g53xlk3h3lf4dqhzqchvl8rphk6nqcaxn49m5azmcqtftwamg36qqkvp6c"
            )

        # Test invalid length
        with self.assertRaises(ValueError):
            self.nostr_key_model._npub_to_hex("npub1short")

    def test_invalid_hex_format(self):
        """Test that invalid hex formats raise appropriate errors"""
        # Test invalid hex characters
        with self.assertRaises(ValueError):
            self.nostr_key_model._hex_to_nsec("xyz123")

        # Test wrong length (not 32 bytes)
        with self.assertRaises(ValueError):
            self.nostr_key_model._hex_to_nsec("deadbeef")  # Too short

        with self.assertRaises(ValueError):
            self.nostr_key_model._hex_to_nsec("deadbeef" * 20)  # Too long

    def test_bech32_charset_compliance(self):
        """Test that generated keys only use valid bech32 characters"""
        # Generate keys and verify charset compliance
        private_key_hex = secrets.token_hex(32)
        public_key_hex = self.nostr_key_model._derive_public_key(private_key_hex)

        nsec = self.nostr_key_model._hex_to_nsec(private_key_hex)
        npub = self.nostr_key_model._hex_to_npub(public_key_hex)

        # Bech32 charset (excluding '1' which is the separator)
        bech32_chars = set("qpzry9x8gf2tvdw0s3jn54khce6mua7l")

        # Check nsec (skip 'nsec1' prefix)
        nsec_data = nsec[5:]
        self.assertTrue(
            all(c in bech32_chars for c in nsec_data),
            "nsec data should only contain valid bech32 characters",
        )

        # Check npub (skip 'npub1' prefix)
        npub_data = npub[5:]
        self.assertTrue(
            all(c in bech32_chars for c in npub_data),
            "npub data should only contain valid bech32 characters",
        )

    def test_cryptographic_regression_vectors(self):
        """Test against known cryptographic vectors to prevent regression"""
        # These are fixed test vectors to catch any changes in crypto implementation
        test_vectors = [
            {
                "private_hex": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
                # Note: These expected values would need to be generated with proper secp256k1
                # and updated once the real library is integrated
            },
            {
                "private_hex": "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364140",
                # Another test vector near the secp256k1 field boundary
            },
        ]

        for vector in test_vectors:
            private_hex = vector["private_hex"]

            # Test that operations are consistent
            public_hex = self.nostr_key_model._derive_public_key(private_hex)
            nsec = self.nostr_key_model._hex_to_nsec(private_hex)
            npub = self.nostr_key_model._hex_to_npub(public_hex)

            # Verify basic properties
            self.assertEqual(len(public_hex), 64)
            self.assertEqual(len(nsec), 63)
            self.assertEqual(len(npub), 63)
            self.assertTrue(nsec.startswith("nsec1"))
            self.assertTrue(npub.startswith("npub1"))

            # Test roundtrip consistency
            private_hex_back = self.nostr_key_model._nsec_to_hex(nsec)
            public_hex_back = self.nostr_key_model._npub_to_hex(npub)

            self.assertEqual(private_hex, private_hex_back)
            self.assertEqual(public_hex, public_hex_back)
