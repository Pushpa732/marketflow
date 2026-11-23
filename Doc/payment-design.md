# Payment Design: MarketFlow

MarketFlow records payments. It does not process money. Customers pay the seller directly, and the seller confirms the payment in the system.

## Payment Methods

| Method | How the customer pays | What the system stores |
|---|---|---|
| Cash on delivery | Pays the delivery person in cash | Method, amount, status |
| bKash | Sends money to the seller's bKash number | Method, amount, status, transaction ID |
| Nagad | Sends money to the seller's Nagad number | Method, amount, status, transaction ID |

A shop accepts bKash or Nagad only if the seller has entered a receiving number. Cash on delivery is always accepted.

## Payment Status (separate from order status)

| Status | Meaning |
|---|---|
| Pending | Waiting for payment or for the seller's check |
| Paid | The seller confirmed the money was received |
| Failed | The seller could not verify the payment |
| Refunded | The money was returned to the customer |

## Rules

- One payment record per order. A cart with two shops creates two orders and two payments.
- One payment method per checkout. It must be accepted by every shop in the cart.
- The payment amount is a copy of the order total.
- A transaction ID can be used only once per method, so one transfer cannot be claimed for several orders.
- The customer can correct a transaction ID while the payment is Pending. After the seller marks it Paid or Failed, it is locked.
- The system never asks for or stores PINs, passwords, or card numbers.

## Limitations

- Transaction IDs are checked by the seller, not automatically. Automatic verification needs a payment gateway agreement with bKash or Nagad, which is planned as a future enhancement.