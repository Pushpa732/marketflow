# Project Progress Report: MarketFlow

Project: Design and Development of a Multi-Vendor E-Commerce and Business Management Software System
Prepared by: Sadia Tarannum Pushpa
Status: Day 36 of 60 (Phase 5 complete)

## 1. Summary

MarketFlow is a multi-vendor marketplace in which small businesses open online shops and customers buy from several shops in one checkout. The complete customer journey is now working: browsing, searching, filtering, cart, delivery address, checkout, order placement, and payment recording. The business owner can manage the shop, products, images, and bulk CSV import. The next phase gives business owners the tools to handle the orders they receive.

## 2. Progress against the 60-Day Plan

| Phase | Days | Status |
|---|---|---|
| 1. Analysis and design | 1 to 6 | Complete: requirements document, use case diagram, ER diagram, architecture |
| 2. Accounts and shops | 7 to 13 | Complete |
| 3. Catalog | 14 to 22 | Complete (products, images, CSV import) |
| 4. Marketplace | 23 to 28 | Complete (listing, search, filters, sorting) |
| 5. Cart and checkout | 29 to 36 | Complete (cart, addresses, checkout, orders, payment records) |
| 6. Order management | 37 to 42 | Next |
| 7. Reviews and reports | 43 to 47 | Planned |
| 8. AI features | 48 to 51 | Planned |
| 9. Testing and security | 52 to 55 | Planned |
| 10. Deployment and documentation | 56 to 60 | Planned |

## 3. What Has Been Built

### 3.1 Accounts and access control
- Registration as customer or business owner; the administrator role cannot be chosen at registration.
- Login and logout with hashed passwords.
- Role-based access: every protected page is checked on the server.

### 3.2 Shops (business owners)
- Shop profile with logo, description, category, and contact details.
- Publish and unpublish; a description is required to publish.
- Flat delivery charge per shop (0 to 5,000 BDT) and optional bKash and Nagad receiving numbers.
- Each business owner can see and change only their own shop.

### 3.3 Products
- Add, edit, and delete products with price, stock, category, and low-stock level.
- Up to five images per product, with type and size checks.
- Draft and published states.
- CSV import with a downloadable template; every row is checked, errors are reported by row number, and nothing is saved if any row is invalid.

### 3.4 Marketplace (customers and visitors)
- Home page, product list, shop list, shop pages, and product pages with image gallery.
- Keyword search across products, shops, and categories.
- Filters (category, shop, price range) and sorting, working together with search.
- Draft products and draft shops are never visible to customers.

### 3.5 Cart, addresses, checkout
- Session-based cart that works before login and survives login.
- Items grouped by shop; item totals, delivery charges, and grand total calculated on the server.
- Up to five saved delivery addresses with Bangladesh mobile number validation.
- Checkout with address selection and payment method selection.

### 3.6 Orders
- One order per shop is created from a multi-shop cart, all inside one database transaction (all saved or none).
- Orders keep copies of prices, names, delivery charge, totals, and the delivery address.
- Stock and total are checked again at the moment of ordering; if a seller changes a price during checkout, the order is refused and the customer reviews the new total.
- Customers can view their order history and order details; other customers' orders are not accessible.

### 3.7 Payments
- One payment record per order: cash on delivery, bKash, or Nagad, with status pending, paid, failed, or refunded.
- For bKash and Nagad the customer sees the seller's number and submits the transaction ID; each ID can be used only once per method.
- The system never asks for or stores PINs, passwords, or card details.

### 3.8 Administration
- Django Admin for users, shops, categories, products, orders, and payments.

## 4. Quality and Security

| Area | What was done |
|---|---|
| Automated tests | A large automated test suite covers accounts, shops, catalog, CSV import, marketplace, cart, addresses, checkout, orders, and payments, including a complete customer journey test |
| Test cases | A test case document traces test cases to requirement IDs |
| Seller data isolation | Every seller query is filtered by the logged-in seller's shop |
| Customer privacy | Orders and addresses are filtered by the logged-in customer |
| Server-side calculation | Prices, stock checks, delivery charges, and totals are never taken from the browser |
| Input safety | Forms validated on the server; text is escaped on pages; CSRF protection on all forms |
| Secrets | Secret key and settings kept in environment variables, not in the repository |

## 5. Documents Produced

- Software Requirements Specification (functional and non-functional requirements)
- Use case diagram, ER diagram, architecture document
- Test case document
- Order design and payment design documents
- Requirements Analysis Document (in preparation)

## 6. Key Design Decisions

- One seller owns one shop, and one order belongs to one shop. This keeps seller permissions simple and secure.
- The cart is stored in the session so customers can shop before registering.
- Stock is checked when an order is placed and reduced only when the seller confirms it.
- Order status, payment status, and delivery status are kept separate.
- Payments are recorded, not processed, so no money or credentials are handled.
- Product variants and Excel import were left out of the first version to protect the schedule.

## 7. Not Yet Built

| Feature | Planned phase |
|---|---|
| Business owner order list, confirm and reject, status workflow, stock reduction | Phase 6 |
| Seller update of payment status and delivery details | Phase 6 |
| Customer cancellation of pending orders | Phase 6 |
| Reviews and ratings | Phase 7 |
| Sales reports, best sellers, low-stock list | Phase 7 |
| AI product description drafting and interest-based discovery | Phase 8 |
| Security review and deployment | Phases 9 and 10 |

## 8. Known Limitations

- Uploaded images need persistent storage when deployed; free hosting often deletes local files.
- A session cart belongs to one browser; a customer who changes device starts with an empty cart.
- Search uses simple word matching; it does not rank results or correct spelling.
- Two customers can place orders for the last item; the second order cannot be confirmed by the seller (stock is checked again at confirmation).
- Transaction IDs are checked by the seller, not automatically; automatic verification needs a payment gateway agreement.
- Names written in Bangla produce generic web addresses such as shop-2.