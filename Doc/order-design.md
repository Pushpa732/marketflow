# Order Design: MarketFlow

## Tables

| Table | Purpose |
|---|---|
| Order | One order for one shop, placed by one customer |
| OrderItem | One product line inside an order |

A cart with products from several shops creates one Order per shop. Each seller sees only the orders of their own shop.

## Snapshot Rule

An order stores a copy of everything that could change later, so historical orders never change:

| Copied data | Stored in |
|---|---|
| Product name and unit price | OrderItem |
| Subtotal, delivery charge, total | Order |
| Shipping name, phone, address, city | Order |

## Order Status

| Status | Meaning | Changed by |
|---|---|---|
| Pending | Placed by the customer, waiting for the seller | System, at checkout |
| Confirmed | Seller accepted the order. Stock is reduced at this moment. | Seller |
| Processing | Seller is preparing the goods | Seller |
| Shipped | Seller handed the goods to delivery | Seller |
| Completed | Goods delivered | Seller |
| Rejected | Seller declined the order. Stock is not changed. | Seller |
| Cancelled | Customer cancelled while the order was still pending | Customer |

Allowed changes: Pending to Confirmed, Rejected, or Cancelled; Confirmed to Processing; Processing to Shipped; Shipped to Completed.

Payment status and delivery details are kept in their own tables, separate from the order status.

## Stock Rule

Stock is checked when the order is placed and checked again when the seller confirms it. Stock is reduced only at confirmation, inside a database transaction, so two orders cannot both take the last item.

## Protection Rules

- A customer or shop that has orders cannot be deleted. Accounts are deactivated and shops are unpublished instead.
- Deleting a product keeps old orders intact, because the order item keeps its own copy of the name and price.
- The database refuses an order item with a quantity below 1.
- Order numbers are random, so they cannot be guessed by counting.

## Placing an Order

When the customer clicks Place order, the server does the following inside one database transaction:

1. Reads the cart and the current prices from the database. The browser never sends prices.
2. Checks that the chosen address belongs to the logged-in customer.
3. Locks the products and checks stock and availability again.
4. Creates one Order per shop, with copied prices, delivery charge, and delivery address.
5. Compares the grand total with the total the customer saw on the checkout page. If they differ (for example the seller changed a price a moment ago), everything is cancelled and the customer is asked to review the new total.

If any step fails, nothing is saved. The cart is cleared only after all orders are saved.

## Known Limitations

- Stock is checked at placement but reduced only when the seller confirms, so two customers can place orders for the last item. The seller's confirmation checks stock again, and the second order cannot be confirmed.
- Database row locking is applied on production databases such as PostgreSQL. The development database (SQLite) serializes writes by itself.