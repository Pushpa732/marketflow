# Project Progress: MarketFlow

## Module Status

| Module | Status | Notes |
|---|---|---|
| User authentication and authorization | Done | Registration, login, logout, role-based access (customer, seller, administrator) |
| Business and shop management | Done | Shop profile, logo upload, publish and unpublish |
| Product and category management | Mostly done | Add, edit, delete, images, low-stock badge. CSV import planned. |
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
| Testing | In progress | Automated tests for accounts, shops, and catalog |

## Design Decisions Made During Development

- One seller owns one shop (MVP simplification).
- A seller's data is isolated on the server: every query filters by the logged-in seller's shop.
- Product variants (such as size and color) are not part of the first version.
- Administrator accounts cannot be created through public registration.
- Uploaded images are stored on the local file system during development.

## Known Limitations So Far

- Uploaded images need persistent storage when deployed. Free hosting often deletes local files, so deployment will need a media storage plan.
- Search, cart, checkout, and orders are not built yet.