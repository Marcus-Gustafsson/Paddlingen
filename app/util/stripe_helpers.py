"""Helpers for loading Stripe Checkout configuration safely.

This module keeps Stripe-related configuration in one place so later Checkout
and webhook steps can reuse the same validation rules instead of reading
environment variables directly in multiple routes.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, cast
from urllib.parse import quote, urlsplit

from flask import current_app
import stripe


@dataclass(frozen=True)
class StripeCheckoutConfiguration:
    """Store the Stripe values needed for the first Checkout integration.

    Attributes:
        secret_key: Secret API key used by the backend to call Stripe.
        webhook_secret: Signing secret used later to verify Stripe webhooks.
        public_base_url: Root public URL used to build success and cancel
            return URLs.
        checkout_product_id: Optional Stripe Product ID used only to fetch the
            hosted Checkout product image from the Dashboard catalog. The app
            still keeps the dynamic canoe title and price note inline.
    """

    secret_key: str
    webhook_secret: str
    public_base_url: str
    checkout_product_id: str | None = None

    def build_success_url(self, booking_reference: str) -> str:
        """Return the Checkout success URL with order and session references.

        Args:
            booking_reference: Local public booking reference stored on the
                pending booking order.

        Returns:
            str: Success return URL that includes both the local booking
            reference and Stripe's session placeholder.
        """

        query_string = (
            f"order_ref={quote(booking_reference)}" "&session_id={CHECKOUT_SESSION_ID}"
        )
        return f"{self.public_base_url}/payment-success?{query_string}"

    def build_cancel_url(self, booking_reference: str) -> str:
        """Return the Checkout cancel URL for one local booking reference.

        Args:
            booking_reference: Local public booking reference stored on the
                pending booking order.

        Returns:
            str: Cancel return URL that lets the app identify which temporary
            order should be released.
        """

        query_string = f"order_ref={quote(booking_reference)}"
        return f"{self.public_base_url}/payment-cancel?{query_string}"


def normalize_stripe_public_base_url(public_base_url: str) -> str:
    """Validate and normalize the configured public site base URL.

    Args:
        public_base_url: URL read from app configuration or the environment.

    Returns:
        The normalized root URL without a trailing slash.

    Raises:
        RuntimeError: If the URL is empty, not HTTP(S), or includes a path,
            query string, or fragment. For this project we want only the public
            site root, such as ``https://example.com``.
    """

    normalized_base_url = public_base_url.strip().rstrip("/")
    parsed_url = urlsplit(normalized_base_url)

    if not normalized_base_url:
        raise RuntimeError("STRIPE_PUBLIC_BASE_URL is missing.")

    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise RuntimeError(
            "STRIPE_PUBLIC_BASE_URL must start with http:// or https:// and "
            "include a hostname."
        )

    if parsed_url.path not in {"", "/"} or parsed_url.query or parsed_url.fragment:
        raise RuntimeError(
            "STRIPE_PUBLIC_BASE_URL must be only the site root, such as "
            "https://example.com."
        )

    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def get_stripe_checkout_configuration_from_mapping(
    config_mapping: Mapping[str, Any],
) -> StripeCheckoutConfiguration:
    """Build validated Stripe Checkout configuration from a mapping.

    Args:
        config_mapping: Usually ``app.config`` or a test dictionary.

    Returns:
        A validated :class:`StripeCheckoutConfiguration` instance.

    Raises:
        RuntimeError: If one or more required values are missing or invalid.
    """

    secret_key = str(config_mapping.get("STRIPE_SECRET_KEY") or "").strip()
    webhook_secret = str(config_mapping.get("STRIPE_WEBHOOK_SECRET") or "").strip()
    public_base_url = str(config_mapping.get("STRIPE_PUBLIC_BASE_URL") or "").strip()
    checkout_product_id = str(
        config_mapping.get("STRIPE_CHECKOUT_PRODUCT_ID") or ""
    ).strip()

    missing_settings: list[str] = []
    if not secret_key:
        missing_settings.append("STRIPE_SECRET_KEY")
    if not webhook_secret:
        missing_settings.append("STRIPE_WEBHOOK_SECRET")
    if not public_base_url:
        missing_settings.append("STRIPE_PUBLIC_BASE_URL")

    if missing_settings:
        missing_values = ", ".join(missing_settings)
        raise RuntimeError(
            "Stripe Checkout is not configured. Missing required setting(s): "
            f"{missing_values}."
        )

    return StripeCheckoutConfiguration(
        secret_key=secret_key,
        webhook_secret=webhook_secret,
        public_base_url=normalize_stripe_public_base_url(public_base_url),
        checkout_product_id=checkout_product_id or None,
    )


def get_stripe_checkout_configuration() -> StripeCheckoutConfiguration:
    """Return validated Stripe Checkout configuration from the current app."""

    return get_stripe_checkout_configuration_from_mapping(current_app.config)


def is_stripe_checkout_configured() -> bool:
    """Return whether Stripe Checkout has all required configuration values."""

    try:
        get_stripe_checkout_configuration()
    except RuntimeError:
        return False
    return True


def build_stripe_client() -> stripe.StripeClient:
    """Return a Stripe client configured with the current app's secret key."""

    stripe_configuration = get_stripe_checkout_configuration()
    return stripe.StripeClient(stripe_configuration.secret_key)


def build_stripe_checkout_product_image_url(public_base_url: str) -> str:
    """Return the public absolute product-image URL used on Checkout."""

    return f"{public_base_url}/static/images/canoe_checkout_icon_png.png"


def can_use_public_base_url_for_checkout_product_image(public_base_url: str) -> bool:
    """Return whether Stripe can realistically fetch a checkout image from the URL.

    Hosted Stripe Checkout can only show the image if Stripe's servers can reach
    it. Local addresses such as ``127.0.0.1`` and ``localhost`` work in the
    browser but are not public to Stripe itself.
    """

    hostname = urlsplit(public_base_url).hostname
    return hostname not in {None, "", "127.0.0.1", "localhost", "0.0.0.0"}


def get_catalog_product_image_urls(
    stripe_client: stripe.StripeClient,
    checkout_product_id: str,
) -> list[str]:
    """Return image URLs from one Stripe Dashboard product when available."""

    stripe_product = stripe_client.v1.products.retrieve(checkout_product_id)
    product_images = getattr(stripe_product, "images", None)
    if not isinstance(product_images, list):
        return []

    cleaned_image_urls: list[str] = []
    for image_url in product_images:
        image_url_text = str(image_url).strip()
        if image_url_text:
            cleaned_image_urls.append(image_url_text)

    return cleaned_image_urls


def get_checkout_product_image_urls(
    stripe_client: stripe.StripeClient,
    stripe_configuration: StripeCheckoutConfiguration,
) -> list[str]:
    """Return the best available product images for hosted Checkout.

    The preferred source is a real Stripe Dashboard product because that lets
    admins manage the image from Stripe without changing code. If no dashboard
    product is configured, the app falls back to its own PNG only when the
    configured public base URL is actually reachable by Stripe.
    """

    checkout_product_id = stripe_configuration.checkout_product_id
    if checkout_product_id:
        try:
            catalog_image_urls = get_catalog_product_image_urls(
                stripe_client,
                checkout_product_id,
            )
        except stripe.StripeError:
            current_app.logger.warning(
                "Could not load Stripe catalog product image for hosted Checkout.",
                extra={"stripe_checkout_product_id": checkout_product_id},
            )
        else:
            if catalog_image_urls:
                return catalog_image_urls

    if not can_use_public_base_url_for_checkout_product_image(
        stripe_configuration.public_base_url
    ):
        return []

    return [
        build_stripe_checkout_product_image_url(stripe_configuration.public_base_url)
    ]


def enrich_checkout_line_items_for_hosted_checkout(
    stripe_line_items: list[dict[str, object]],
    image_urls: list[str],
) -> list[dict[str, object]]:
    """Add hosted-Checkout-friendly product details to server-approved line items."""

    enriched_line_items = deepcopy(stripe_line_items)
    if not image_urls:
        return enriched_line_items

    for line_item in enriched_line_items:
        price_data = line_item.get("price_data")
        if not isinstance(price_data, dict):
            continue

        product_data = price_data.get("product_data")
        if not isinstance(product_data, dict):
            continue

        if not product_data.get("images"):
            product_data["images"] = list(image_urls)

    return enriched_line_items


def create_stripe_checkout_session(
    public_booking_reference: str,
    stripe_line_items: list[dict[str, object]],
    metadata: Mapping[str, str],
    payment_intent_description: str | None = None,
) -> stripe.checkout.Session:
    """Create one hosted Stripe Checkout Session for a local booking attempt.

    Args:
        public_booking_reference: Local booking reference used in redirect URLs.
        stripe_line_items: Server-approved Stripe line items for the booking.
        metadata: Local identifiers stored on the Stripe session for later
            lookup and webhook handling.
        payment_intent_description: Optional short receipt description shown by
            Stripe in the successful payment receipt email.

    Returns:
        stripe.checkout.Session: Newly created Stripe Checkout Session.
    """

    stripe_configuration = get_stripe_checkout_configuration()
    stripe_client = build_stripe_client()
    product_image_urls = get_checkout_product_image_urls(
        stripe_client,
        stripe_configuration,
    )
    hosted_checkout_line_items = enrich_checkout_line_items_for_hosted_checkout(
        stripe_line_items,
        product_image_urls,
    )
    checkout_payload: dict[str, Any] = {
        "mode": "payment",
        "locale": "sv",
        "payment_method_types": ["card"],
        "submit_type": "book",
        "client_reference_id": public_booking_reference,
        "success_url": stripe_configuration.build_success_url(public_booking_reference),
        "cancel_url": stripe_configuration.build_cancel_url(public_booking_reference),
        "line_items": cast(Any, hosted_checkout_line_items),
        "metadata": dict(metadata),
        "custom_text": {
            "submit": {
                "message": (
                    "Reservationen blir bindande först när betalningen är slutförd."
                )
            },
            "after_submit": {
                "message": (
                    "Du skickas tillbaka till Paddlingen direkt efter betalningen "
                    "för bokningsbekräftelse och översikt."
                )
            },
        },
        # Stripe only allows expires_at between 30 minutes and 24 hours
        # from session creation. The local booking hold is shorter and is
        # enforced by the app before the visitor enters Stripe Checkout.
        "expires_at": int(
            (datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp()
        ),
    }
    if payment_intent_description:
        checkout_payload["payment_intent_data"] = {
            "description": payment_intent_description,
        }

    return stripe_client.v1.checkout.sessions.create(cast(Any, checkout_payload))


def retrieve_stripe_checkout_session(
    checkout_session_id: str,
) -> stripe.checkout.Session:
    """Retrieve one Stripe Checkout Session by ID."""

    stripe_client = build_stripe_client()
    return stripe_client.v1.checkout.sessions.retrieve(checkout_session_id)


def expire_stripe_checkout_session(
    checkout_session_id: str,
) -> stripe.checkout.Session:
    """Expire one open Stripe Checkout Session by ID.

    Args:
        checkout_session_id: Stripe Checkout Session ID such as ``cs_test_...``.

    Returns:
        stripe.checkout.Session: Updated Checkout Session after Stripe expires
        it.
    """

    stripe_client = build_stripe_client()
    return stripe_client.v1.checkout.sessions.expire(checkout_session_id)


def construct_stripe_webhook_event(
    payload: bytes,
    stripe_signature_header: str,
) -> stripe.Event:
    """Verify and parse one incoming Stripe webhook event.

    Args:
        payload: Raw request body exactly as Flask received it.
        stripe_signature_header: Value from the incoming
            ``Stripe-Signature`` header.

    Returns:
        stripe.Event: Verified Stripe event object.

    Raises:
        ValueError: If the payload cannot be parsed as a Stripe event.
        stripe.SignatureVerificationError: If the signature does not match the
            configured webhook secret.
    """

    stripe_configuration = get_stripe_checkout_configuration()
    return stripe.Webhook.construct_event(
        payload=payload,
        sig_header=stripe_signature_header,
        secret=stripe_configuration.webhook_secret,
    )
