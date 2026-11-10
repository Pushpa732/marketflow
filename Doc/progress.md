# Project Progress: MarketFlow

## Module Status

| Module | Status | Notes |
|---|---|---|
| User authentication and authorization | Done | Registration, login, logout, role-based access (customer, seller, administrator) |
| Business and shop management | Done | Shop profile, logo upload, publish and unpublish |
| Product and category management | Done | Add, edit, delete, up to 5 images, low-stock badge, CSV import with validation |
| Marketplace and search | Done | Home page, product and shop listings, shop page, product page, keyword search, filters (category, shop, price), sorting, pagination |
| Shopping cart and checkout | Planned | One order per shop at checkout |
| Order management | Planned | Status workflow, stock deduction on confirmation |
| Inventory management | Partly done | Stock field and low-stock alert done. Stock deduction planned with orders. |
| Payment record management | Planned | Cash on delivery, bKash, Nagad (records only) |
| Delivery and tracking | Planned | |
| Reviews and ratings | Planned | Only for delivered purchases |
| Reports and analytics | Planned | |
| AI assistance | Planned | Product descriptions and interest-based discovery |
| Administrator management | Done (basic) | Django Admin for users, shops, categories, products |
| Testing | In progress | Automated tests for accounts, shops, catalog, CSV import, and marketplace |

## Design Decisions Made During Development

- One seller owns one shop (MVP simplification).
- A seller's data is isolated on the server: every query filters by the logged-in seller's shop.
- Product variants (such as size and color) are not part of the first version.
- Administrator accounts cannot be created through public registration.
- CSV import is all-or-nothing: if any row is invalid, nothing is saved, which prevents duplicates when the seller fixes and re-uploads the file.
- CSV files cannot choose the shop; products always go to the logged-in seller's shop.
- Customers see only published products of published shops. The rule is defined in one function and reused by every public page.
- Search, filters, and sorting share one validated form, so invalid input gives a clear message instead of an error.
- Every sort order has a tie-breaker so pagination never repeats or skips products.
- Uploaded images are stored on the local file system during development.

## Known Limitations So Far

- Uploaded images need persistent storage when deployed. Free hosting often deletes local files, so deployment will need a media storage plan.
- Only CSV import is supported. Excel (.xlsx) import is left for future work.
- CSV import does not upload product images. Images are added per product afterwards.
- Search uses simple word matching. It does not rank by relevance or correct spelling mistakes. Database full-text search and AI interpretation are planned improvements.
- Shop and product addresses use English letters and digits only, so names written in Bangla produce generic addresses such as "shop-2".
- Cart, checkout, and orders are not built yet.

## Update: Phase 5 (Cart and Checkout, in progress)

- **Done:** session-based shopping cart (add, update, remove, items grouped by shop, server-side totals, cart count in the navigation bar).
- **Design decision:** the cart is stored in the visitor's session instead of a database table, so customers can add items before logging in. The session is kept when the customer logs in. The `Cart` and `CartItem` tables in the first ER diagram are therefore not used. The ER diagram will be updated when the order tables are finished.
- **Limitation:** a session cart belongs to one browser. A customer who changes device starts with an empty cart. A database cart is a possible future improvement.
- **Rule:** prices, stock, and totals are always read from the database. The browser never sends a price.
- **Planned:** delivery address, checkout page, orders and order items (price snapshot), one order per shop, payment records.