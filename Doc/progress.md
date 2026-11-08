# Project Progress: MarketFlow

## Module Status

| Module | Status | Notes |
|---|---|---|
| User authentication and authorization | Done | Registration, login, logout, role-based access (customer, seller, administrator) |
| Business and shop management | Done | Shop profile, logo upload, publish and unpublish |
| Product and category management | Done | Add, edit, delete, up to 5 images, low-stock badge, CSV import with validation |
| Marketplace and search | Started | Home page lists published shops. Search and filters planned. |
| Shopping cart and checkout | Planned | One order per shop at checkout |
| Order management | Planned | Status workflow, stock deduction on confirmation |
| Inventory management | Partly done | Stock field and low-stock alert done. Stock deduction planned with orders. |
| Payment record management | Planned | Cash on delivery, bKash, Nagad (records only) |
| Delivery and tracking | Planned | |
| Reviews and ratings | Planned | Only for delivered purchases |
| Reports and analytics | Planned | |
| AI assistance | Planned | Product descriptions and interest-based discovery |
| Administrator management | Done (basic) | Django Admin for users, shops, categories, products |
| Testing | In progress | Automated tests for accounts, shops, catalog, and CSV import |

## Design Decisions Made During Development

- One seller owns one shop (MVP simplification).
- A seller's data is isolated on the server: every query filters by the logged-in seller's shop.
- Product variants (such as size and color) are not part of the first version.
- Administrator accounts cannot be created through public registration.
- CSV import is all-or-nothing: if any row is invalid, nothing is saved, which prevents duplicates when the seller fixes and re-uploads the file.
- CSV files cannot choose the shop; products always go to the logged-in seller's shop.
- Uploaded images are stored on the local file system during development.

## Known Limitations So Far

- Uploaded images need persistent storage when deployed. Free hosting often deletes local files, so deployment will need a media storage plan.
- Only CSV import is supported. Excel (.xlsx) import is left for future work.
- CSV import does not upload product images. Images are added per product afterwards.
- Search, cart, checkout, and orders are not built yet.