# Checkout Context

Checkout currently supports cart review, shipping address, payment confirmation, and order creation.

Relevant product rules:
- Users must be authenticated before payment.
- Backend calculates final price, discount, tax, and shipping fee.
- Frontend only displays totals returned by backend.
- Orders must not be created twice if a user retries payment.

Failure modes:
- Payment provider timeout should show a retry message.
- Inventory mismatch should block order creation and ask the user to update cart.
- Invalid coupon should not block checkout, but must show a clear warning.

QA expectations:
- Test successful checkout.
- Test payment failure.
- Test duplicate submit protection.
- Test invalid coupon and inventory mismatch.
