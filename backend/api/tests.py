from django.test import TestCase
from .services import validate_price
class PriceValidationTests(TestCase):
    def test_valid_price(self): self.assertEqual(str(validate_price('25.50')),'25.50')
    def test_negative_price_rejected(self):
        with self.assertRaises(ValueError): validate_price('-1')
