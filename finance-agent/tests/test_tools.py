import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
import httpx

from auth import UserContext
from tools import get_toolkit


class ToolAuthorizationTests(unittest.TestCase):
    def test_tools_require_a_token(self):
        tools, _ = get_toolkit()
        for tool in tools.values():
            with self.subTest(tool=tool.__name__):
                with self.assertRaises(HTTPException) as error:
                    tool()
                self.assertEqual(error.exception.status_code, 401)

    def test_tools_revalidate_token_before_backend_access(self):
        tools, _ = get_toolkit({"user_id": "segun2", "token": "invalid-token"})
        with patch("tools.user_from_token", side_effect=HTTPException(status_code=401)), \
                patch("tools.httpx.Client") as client:
            for tool in tools.values():
                with self.subTest(tool=tool.__name__):
                    with self.assertRaises(HTTPException) as error:
                        tool()
                    self.assertEqual(error.exception.status_code, 401)
            client.assert_not_called()

    def test_context_cannot_select_another_user(self):
        tools, _ = get_toolkit({"user_id": "other-user", "token": "valid-token"})
        authenticated_user = UserContext(user_id="segun2", subject="keycloak-sub", token="valid-token")
        with patch("tools.user_from_token", return_value=authenticated_user), \
                patch("tools.httpx.Client") as client:
            with self.assertRaises(HTTPException) as error:
                tools["get_balance"]()
        self.assertEqual(error.exception.status_code, 403)
        client.assert_not_called()

    def test_balance_uses_verified_user_and_forwards_token(self):
        tools, _ = get_toolkit({"user_id": "segun2", "token": "valid-token"})
        authenticated_user = UserContext(user_id="segun2", subject="keycloak-sub", token="valid-token")
        response = MagicMock()
        response.json.return_value = {"balance": 123.4}
        client = MagicMock()
        client.__enter__.return_value = client
        client.get.return_value = response
        with patch("tools.user_from_token", return_value=authenticated_user), \
                patch("tools._tx_base", return_value="http://transaction-service:8080"), \
                patch("tools.httpx.Client", return_value=client):
            result = tools["get_balance"]()

        self.assertEqual(result, {
            "account_id": "segun2",
            "currency": "GBP",
            "balance": "123.40",
            "mock": False,
        })
        client.get.assert_called_once_with(
            "http://transaction-service:8080/balance/segun2",
            headers={"Authorization": "Bearer valid-token"},
        )

    def test_recent_transactions_are_scoped_to_verified_user(self):
        tools, _ = get_toolkit({"user_id": "segun2", "token": "valid-token"})
        authenticated_user = UserContext(user_id="segun2", subject="keycloak-sub", token="valid-token")
        response = MagicMock()
        response.json.return_value = [{"transactionType": "DEPOSIT", "amount": 25}]
        client = MagicMock()
        client.__enter__.return_value = client
        client.get.return_value = response
        with patch("tools.user_from_token", return_value=authenticated_user), \
                patch("tools._tx_base", return_value="http://transaction-service:8080"), \
                patch("tools.httpx.Client", return_value=client):
            result = tools["get_recent_transactions"]()

        self.assertEqual(result["transactions"], response.json.return_value)
        self.assertFalse(result["mock"])
        client.get.assert_called_once_with(
            "http://transaction-service:8080/transactions/segun2",
            headers={"Authorization": "Bearer valid-token"},
        )

    def test_backend_errors_do_not_fall_back_to_mock_data(self):
        tools, _ = get_toolkit({"user_id": "segun2", "token": "valid-token"})
        authenticated_user = UserContext(user_id="segun2", subject="keycloak-sub", token="valid-token")
        client = MagicMock()
        client.__enter__.return_value = client
        client.get.side_effect = httpx.ConnectError("network failure")
        with patch("tools.user_from_token", return_value=authenticated_user), \
                patch("tools._tx_base", return_value="http://transaction-service:8080"), \
                patch("tools.httpx.Client", return_value=client):
            with self.assertRaises(HTTPException) as error:
                tools["get_balance"]()
        self.assertEqual(error.exception.status_code, 502)


if __name__ == "__main__":
    unittest.main()
