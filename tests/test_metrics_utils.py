import os
import importlib
import sys
import unittest

# Ensure the backend package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class MetricsUtilsTest(unittest.TestCase):
    def setUp(self):
        # Remove module if already loaded to force re-import with env changes
        if 'backend.metrics_utils' in sys.modules:
            del sys.modules['backend.metrics_utils']

    def test_sanitize_email_url_phone_card(self):
        import backend.metrics_utils as metrics_utils
        # Email
        s = "Contact: john.doe@example.com"
        out = metrics_utils.sanitize_prompt(s)
        self.assertIn("<REDACTED_EMAIL>", out)

        # URL
        s2 = "Visit http://example.com/path"
        out2 = metrics_utils.sanitize_prompt(s2)
        self.assertIn("<REDACTED_URL>", out2)

        # Phone
        s3 = "Call me at +1 555-123-4567"
        out3 = metrics_utils.sanitize_prompt(s3)
        self.assertIn("<REDACTED_PHONE>", out3)

        # Card-like number
        s4 = "Card 4111 1111 1111 1111"
        out4 = metrics_utils.sanitize_prompt(s4)
        self.assertIn("<REDACTED_NUMBER>", out4)

    def test_extra_patterns_env(self):
        # Set extra pattern and reload module
        os.environ['METRICS_SANITIZE_EXTRA'] = r"SECRET(\d+):::<SNUM>"
        if 'backend.metrics_utils' in sys.modules:
            del sys.modules['backend.metrics_utils']
        import backend.metrics_utils as metrics_utils
        importlib.reload(metrics_utils)
        s = "This is SECRET12345 in text"
        out = metrics_utils.sanitize_prompt(s)
        self.assertIn("<SNUM>", out)
        # cleanup
        del os.environ['METRICS_SANITIZE_EXTRA']

    def test_encrypt_decrypt(self):
        # enable encryption
        try:
            from cryptography.fernet import Fernet
        except Exception:
            self.skipTest('cryptography not available')

        key = Fernet.generate_key().decode('utf-8')
        os.environ['METRICS_ENCRYPT_PROMPT'] = 'true'
        os.environ['METRICS_ENCRYPTION_KEY'] = key

        if 'backend.metrics_utils' in sys.modules:
            del sys.modules['backend.metrics_utils']
        import backend.metrics_utils as metrics_utils
        importlib.reload(metrics_utils)

        plain = 'Hello john.doe@example.com and visit http://x.com'
        sanitized = metrics_utils.sanitize_prompt(plain)
        enc = metrics_utils.encrypt_text(sanitized)
        self.assertIsNotNone(enc)
        dec = metrics_utils.decrypt_text(enc)
        self.assertIsNotNone(dec)
        # decrypted should equal sanitized
        self.assertEqual(dec, sanitized)

        # cleanup
        del os.environ['METRICS_ENCRYPT_PROMPT']
        del os.environ['METRICS_ENCRYPTION_KEY']

if __name__ == '__main__':
    unittest.main()
