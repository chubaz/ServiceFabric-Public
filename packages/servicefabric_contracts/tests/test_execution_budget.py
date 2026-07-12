import unittest
from pydantic import ValidationError
from servicefabric_contracts.budgets import ExecutionBudget, MonetaryBudget
class BudgetTests(unittest.TestCase):
    def test_negative_and_float_money_are_rejected(self):
        with self.assertRaises(ValidationError): ExecutionBudget(maximum_provider_calls=-1)
        with self.assertRaises(ValidationError): MonetaryBudget(amount=1.2, currency="EUR")
