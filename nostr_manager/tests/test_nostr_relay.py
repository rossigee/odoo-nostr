# -*- coding: utf-8 -*-

from unittest.mock import MagicMock, patch

import requests
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestNostrRelay(TransactionCase):
    """Test Nostr relay management functionality"""

    def setUp(self):
        super().setUp()
        self.relay_model = self.env["nostr.relay"]

    def test_relay_creation_basic(self):
        """Test basic relay creation"""
        relay = self.relay_model.create(
            {
                "name": "Test Relay",
                "url": "wss://test.relay.com",
                "description": "Test relay for unit testing",
            }
        )

        self.assertEqual(relay.name, "Test Relay")
        self.assertEqual(relay.url, "wss://test.relay.com")
        self.assertTrue(relay.is_active)
        self.assertTrue(relay.is_read)
        self.assertTrue(relay.is_write)
        self.assertEqual(relay.connection_status, "unknown")
        self.assertEqual(relay.event_count_read, 0)
        self.assertEqual(relay.event_count_write, 0)

    def test_relay_url_validation(self):
        """Test relay URL format validation"""
        # Valid WebSocket URLs
        valid_urls = [
            "wss://relay.example.com",
            "ws://localhost:8080",
            "wss://relay.example.com:443/path",
        ]

        for url in valid_urls:
            relay = self.relay_model.create({"name": f"Test {url}", "url": url})
            self.assertEqual(relay.url, url)

    def test_relay_url_validation_errors(self):
        """Test that invalid URLs are rejected"""
        invalid_urls = [
            "http://relay.example.com",  # Wrong protocol
            "https://relay.example.com",  # Wrong protocol
            "ftp://relay.example.com",  # Wrong protocol
            "relay.example.com",  # No protocol
            "",  # Empty
        ]

        for url in invalid_urls:
            with self.assertRaises(ValidationError):
                self.relay_model.create({"name": f"Invalid {url}", "url": url})

    def test_unique_url_constraint(self):
        """Test that duplicate relay URLs are not allowed"""
        # Create first relay
        self.relay_model.create(
            {"name": "First Relay", "url": "wss://unique.relay.com"}
        )

        # Try to create second relay with same URL - should fail
        with self.assertRaises(Exception):  # Database constraint error
            self.relay_model.create(
                {"name": "Duplicate Relay", "url": "wss://unique.relay.com"}
            )

    @patch("requests.get")
    def test_relay_connection_test_success(self, mock_get):
        """Test successful relay connection testing"""
        # Mock successful HTTP response with NIP-11 data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "Test Relay Server",
            "description": "A test relay for Nostr",
            "supported_nips": [1, 2, 9, 11, 12, 15, 16, 20],
            "software": "test-relay",
            "version": "1.0.0",
        }
        mock_get.return_value = mock_response

        relay = self.relay_model.create(
            {"name": "Connection Test Relay", "url": "wss://test-connection.relay.com"}
        )

        result = relay.action_test_connection()

        # Should update connection status and relay info
        self.assertEqual(relay.connection_status, "connected")
        self.assertIn("Test Relay Server", relay.relay_info)
        self.assertIn("1,2,9,11,12,15,16,20", relay.supported_nips)

        # Should return notification action
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")

    @patch("requests.get")
    def test_relay_connection_test_failure(self, mock_get):
        """Test failed relay connection testing"""
        # Mock failed HTTP response
        mock_get.side_effect = Exception("Connection failed")

        relay = self.relay_model.create(
            {"name": "Failed Connection Relay", "url": "wss://unreachable.relay.com"}
        )

        result = relay.action_test_connection()

        # Should update connection status to error
        self.assertEqual(relay.connection_status, "error")

        # Should return error notification
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertIn("Failed to connect", result["params"]["message"])

    @patch("requests.get")
    def test_relay_nip11_info_parsing(self, mock_get):
        """Test NIP-11 relay information parsing"""
        # Mock NIP-11 response
        nip11_data = {
            "name": "Advanced Test Relay",
            "description": "A feature-rich relay for testing",
            "pubkey": "relay_pubkey_here",
            "contact": "admin@relay.com",
            "supported_nips": [1, 2, 9, 11, 12, 15, 16, 20, 22, 26, 28, 33],
            "software": "strfry",
            "version": "0.9.6",
            "limitation": {
                "max_message_length": 65536,
                "max_subscriptions": 20,
                "max_filters": 100,
            },
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = nip11_data
        mock_get.return_value = mock_response

        relay = self.relay_model.create(
            {"name": "NIP-11 Test Relay", "url": "wss://nip11-test.relay.com"}
        )

        relay.action_test_connection()

        # Verify NIP-11 data was parsed correctly
        self.assertIn("Advanced Test Relay", relay.relay_info)
        self.assertIn("strfry", relay.relay_info)
        self.assertIn("admin@relay.com", relay.relay_info)
        self.assertEqual(relay.supported_nips, "1,2,9,11,12,15,16,20,22,26,28,33")

    def test_relay_event_counters(self):
        """Test relay event read/write counters"""
        relay = self.relay_model.create(
            {"name": "Counter Test Relay", "url": "wss://counter-test.relay.com"}
        )

        # Initial counters should be 0
        self.assertEqual(relay.event_count_read, 0)
        self.assertEqual(relay.event_count_write, 0)

        # Increment read counter
        relay.increment_read_count()
        self.assertEqual(relay.event_count_read, 1)
        self.assertEqual(relay.event_count_write, 0)

        # Increment write counter
        relay.increment_write_count()
        self.assertEqual(relay.event_count_read, 1)
        self.assertEqual(relay.event_count_write, 1)

        # Multiple increments
        for _ in range(5):
            relay.increment_read_count()
            relay.increment_write_count()

        self.assertEqual(relay.event_count_read, 6)
        self.assertEqual(relay.event_count_write, 6)

    def test_relay_activity_tracking(self):
        """Test that relay changes are tracked in chatter"""
        relay = self.relay_model.create(
            {"name": "Activity Test Relay", "url": "wss://activity-test.relay.com"}
        )

        # Update tracked fields
        relay.write(
            {
                "name": "Updated Activity Test Relay",
                "is_active": False,
                "description": "Updated description",
            }
        )

        # Check that messages were created
        self.assertTrue(
            relay.message_ids, "Relay operations should create activity messages"
        )

    def test_relay_read_write_configuration(self):
        """Test relay read/write configuration options"""
        # Read-only relay
        read_only_relay = self.relay_model.create(
            {
                "name": "Read Only Relay",
                "url": "wss://readonly.relay.com",
                "is_read": True,
                "is_write": False,
            }
        )

        self.assertTrue(read_only_relay.is_read)
        self.assertFalse(read_only_relay.is_write)

        # Write-only relay
        write_only_relay = self.relay_model.create(
            {
                "name": "Write Only Relay",
                "url": "wss://writeonly.relay.com",
                "is_read": False,
                "is_write": True,
            }
        )

        self.assertFalse(write_only_relay.is_read)
        self.assertTrue(write_only_relay.is_write)

    def test_relay_status_field_values(self):
        """Test connection status field values"""
        relay = self.relay_model.create(
            {"name": "Status Test Relay", "url": "wss://status-test.relay.com"}
        )

        # Test all valid status values
        valid_statuses = ["unknown", "connected", "disconnected", "error"]

        for status in valid_statuses:
            relay.write({"connection_status": status})
            self.assertEqual(relay.connection_status, status)

    def test_default_relay_data_loading(self):
        """Test that default relays are properly loaded"""
        # Check if default relays exist (assuming they're created during module install)
        default_relays = self.relay_model.search([])

        # Should have some default relays
        self.assertTrue(len(default_relays) > 0, "Should have default relays loaded")

        # Check for specific known default relays
        damus_relay = self.relay_model.search([("url", "=", "wss://relay.damus.io")])
        if damus_relay:  # Only test if default data was loaded
            self.assertEqual(damus_relay.name, "Damus")
            self.assertTrue(damus_relay.is_active)
            self.assertTrue(damus_relay.is_read)
            self.assertTrue(damus_relay.is_write)

    @patch("requests.get")
    def test_relay_connection_timeout_handling(self, mock_get):
        """Test handling of connection timeouts"""
        # Mock timeout exception
        import requests

        mock_get.side_effect = requests.Timeout("Connection timed out")

        relay = self.relay_model.create(
            {"name": "Timeout Test Relay", "url": "wss://slow.relay.com"}
        )

        result = relay.action_test_connection()

        self.assertEqual(relay.connection_status, "error")
        self.assertIn("timeout", result["params"]["message"].lower())

    def test_relay_search_and_filtering(self):
        """Test relay search and filtering capabilities"""
        # Create test relays with different properties
        active_relay = self.relay_model.create(
            {
                "name": "Active Test Relay",
                "url": "wss://active.test.com",
                "is_active": True,
                "connection_status": "connected",
            }
        )

        inactive_relay = self.relay_model.create(
            {
                "name": "Inactive Test Relay",
                "url": "wss://inactive.test.com",
                "is_active": False,
                "connection_status": "disconnected",
            }
        )

        # Test filtering by active status
        active_relays = self.relay_model.search([("is_active", "=", True)])
        self.assertIn(active_relay, active_relays)
        self.assertNotIn(inactive_relay, active_relays)

        # Test filtering by connection status
        connected_relays = self.relay_model.search(
            [("connection_status", "=", "connected")]
        )
        self.assertIn(active_relay, connected_relays)
        self.assertNotIn(inactive_relay, connected_relays)
