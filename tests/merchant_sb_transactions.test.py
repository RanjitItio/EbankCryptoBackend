import unittest
from blacksheep.testing import TestClient
from app.main import app



class TestSearchMerchantProdTransactions(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_search_transaction_order_id(self):
        response = self.client.get("/api/v2/merchant/search/prod/transactions/", params={"query": "order123"})
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(len(data["merchant_searched_transactions"]) > 0)

    def test_search_transaction_transaction_id(self):
        response = self.client.get("/api/v2/merchant/search/prod/transactions/", params={"query": "trans123"})
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(len(data["merchant_searched_transactions"]) > 0)

    def test_search_transaction_business_name(self):
        response = self.client.get("/api/v2/merchant/search/prod/transactions/", params={"query": "Business ABC"})
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(len(data["merchant_searched_transactions"]) > 0)

    def test_search_transaction_date_range(self):
        response = self.client.get("/api/v2/merchant/search/prod/transactions/", params={"query": "CustomRange", "startDate": "2022-01-01", "endDate": "2022-01-31"})
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(len(data["merchant_searched_transactions"]) > 0)

if __name__ == "__main__":
    unittest.main()