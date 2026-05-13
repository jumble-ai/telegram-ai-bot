from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import httpx


class CryptoPayError(RuntimeError):
    """Raised when Crypto Pay cannot create a usable invoice."""


@dataclass(frozen=True, slots=True)
class DonationInvoice:
    """Crypto Pay invoice for a donation."""

    invoice_id: int
    amount: str
    payment_url: str


@dataclass(frozen=True, slots=True)
class PaymentInvoice:
    """Crypto Pay invoice created from a text request."""

    invoice_id: int
    amount: str
    fiat: str
    accepted_assets: tuple[str, ...]
    payment_url: str


@dataclass(frozen=True, slots=True)
class CryptoPayClient:
    """Minimal async client for Crypto Pay invoices."""

    api_token: str
    base_url: str = "https://pay.crypt.bot/api"

    async def create_donation_invoice(
        self,
        amount_usd: int,
        user_id: int,
    ) -> DonationInvoice:
        """Create a fiat USD donation invoice."""
        payload = {
            "currency_type": "fiat",
            "fiat": "USD",
            "amount": str(amount_usd),
            "description": f"💝 Донат ${amount_usd} для поддержки бота",
            "hidden_message": "Спасибо за поддержку! 💜",
            "payload": f"donation:{user_id}:{amount_usd}",
            "allow_comments": True,
            "allow_anonymous": True,
            "expires_in": 3600,
        }
        headers = {"Crypto-Pay-API-Token": self.api_token}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/createInvoice",
                json=payload,
                headers=headers,
            )

        if response.status_code >= 400:
            msg = f"Crypto Pay request failed with status {response.status_code}."
            raise CryptoPayError(msg)

        return self._parse_invoice(response.json())

    async def create_usd_invoice(
        self,
        amount_usd: Decimal,
        accepted_assets: tuple[str, ...],
        description: str,
        user_id: int,
    ) -> PaymentInvoice:
        """Create a USD invoice payable with selected crypto assets."""
        normalized_amount = _format_amount(amount_usd)
        payload = {
            "currency_type": "fiat",
            "fiat": "USD",
            "accepted_assets": ",".join(accepted_assets),
            "amount": normalized_amount,
            "description": description[:1024],
            "payload": f"invoice:{user_id}:{normalized_amount}",
            "allow_comments": True,
            "allow_anonymous": True,
            "expires_in": 3600,
        }
        headers = {"Crypto-Pay-API-Token": self.api_token}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/createInvoice",
                json=payload,
                headers=headers,
            )

        if response.status_code >= 400:
            msg = f"Crypto Pay request failed with status {response.status_code}."
            raise CryptoPayError(msg)

        return self._parse_payment_invoice(response.json(), accepted_assets)

    @staticmethod
    def _parse_invoice(data: dict[str, Any]) -> DonationInvoice:
        if data.get("ok") is not True:
            raise CryptoPayError("Crypto Pay response is not successful.")

        result = data.get("result")
        if not isinstance(result, dict):
            raise CryptoPayError("Crypto Pay response does not contain invoice.")

        invoice_id = result.get("invoice_id")
        amount = result.get("amount")
        payment_url = result.get("bot_invoice_url") or result.get("pay_url")
        if not isinstance(invoice_id, int):
            raise CryptoPayError("Crypto Pay invoice id has unexpected format.")
        if not isinstance(amount, str):
            raise CryptoPayError("Crypto Pay amount has unexpected format.")
        if not isinstance(payment_url, str) or not payment_url:
            raise CryptoPayError("Crypto Pay invoice URL is missing.")

        return DonationInvoice(
            invoice_id=invoice_id,
            amount=amount,
            payment_url=payment_url,
        )

    @staticmethod
    def _parse_payment_invoice(
        data: dict[str, Any],
        accepted_assets: tuple[str, ...],
    ) -> PaymentInvoice:
        if data.get("ok") is not True:
            raise CryptoPayError("Crypto Pay response is not successful.")

        result = data.get("result")
        if not isinstance(result, dict):
            raise CryptoPayError("Crypto Pay response does not contain invoice.")

        invoice_id = result.get("invoice_id")
        amount = result.get("amount")
        fiat = result.get("fiat")
        payment_url = result.get("bot_invoice_url") or result.get("pay_url")
        if not isinstance(invoice_id, int):
            raise CryptoPayError("Crypto Pay invoice id has unexpected format.")
        if not isinstance(amount, str):
            raise CryptoPayError("Crypto Pay amount has unexpected format.")
        if not isinstance(fiat, str):
            raise CryptoPayError("Crypto Pay fiat has unexpected format.")
        if not isinstance(payment_url, str) or not payment_url:
            raise CryptoPayError("Crypto Pay invoice URL is missing.")

        return PaymentInvoice(
            invoice_id=invoice_id,
            amount=amount,
            fiat=fiat,
            accepted_assets=accepted_assets,
            payment_url=payment_url,
        )


def _format_amount(amount: Decimal) -> str:
    return format(amount.normalize(), "f")
