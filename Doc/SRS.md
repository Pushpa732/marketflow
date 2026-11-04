# Software Requirements Specification (SRS)
## MarketFlow: Multi-Vendor E-Commerce and Business Management System

## 1. Introduction

### 1.1 Purpose
This document specifies the requirements of MarketFlow, a web-based multi-vendor
marketplace where multiple small businesses manage online shops and customers
discover products and place orders.

### 1.2 Scope
MarketFlow allows sellers to manage shops, products, inventory, orders, payment
records, and delivery updates. Customers can browse, search, order, track orders,
and write reviews. Administrators manage users, shops, and categories. The system
also includes limited AI-assisted features.

### 1.3 Intended Users
- Customers
- Sellers (business owners)
- Administrators

### 1.4 Technology
Python, Django, HTML, CSS, Bootstrap, JavaScript, SQLite (development),
PostgreSQL (production), Git and GitHub.

## 2. User Roles

| Role | Description |
|---|---|
| Customer | Browses products, places orders, tracks orders, writes reviews |
| Seller | Manages one shop, its products, orders, and reports |
| Administrator | Manages users, shops, categories, and platform settings |

## 3. Functional Requirements

### 3.1 Customer Requirements

| ID | Requirement |
|---|---|
| FR-C1 | The system shall allow customers to browse shops and products without logging in. |
| FR-C2 | The system shall allow customers to search for products, shops, and categories using keywords. |
| FR-C3 | The system shall allow customers to filter products by category, price, and shop. |
| FR-C4 | The system shall display product details, including images, price, stock status, and seller information. |
| FR-C5 | The system shall display shop ratings and customer reviews. |
| FR-C6 | The system shall allow customers to add products to a shopping cart and update or remove them. |
| FR-C7 | The system shall require customers to register or log in before checkout. |
| FR-C8 | The system shall allow customers to enter delivery address and contact information at checkout. |
| FR-C9 | The system shall allow customers to select a payment method (Cash on Delivery, bKash, or Nagad) and record it. |
| FR-C10 | The system shall create a separate order for each shop when a cart contains products from multiple shops. |
| FR-C11 | The system shall allow customers to view their order history and track order status. |
| FR-C12 | The system shall allow customers to submit a rating and review only for delivered products they purchased. |
| FR-C13 | The system shall prevent customers from viewing other customers' private information and orders. |

### 3.2 Seller Requirements

| ID | Requirement |
|---|---|
| FR-S1 | The system shall allow business owners to register and log in as sellers. |
| FR-S2 | The system shall allow a seller to create and edit a shop profile (name, logo, description, category, contact). |
| FR-S3 | The system shall allow a seller to add, edit, delete, and publish products. |
| FR-S4 | The system shall allow a seller to upload product images and manage price, category, and stock. |
| FR-S5 | The system shall allow a seller to import product data from a CSV file and report invalid rows. |
| FR-S6 | The system shall allow a seller to view incoming orders for their own shop only. |
| FR-S7 | The system shall allow a seller to confirm, reject, process, ship, or complete an order. |
| FR-S8 | The system shall check stock before confirming an order and reduce stock when the order is confirmed. |
| FR-S9 | The system shall allow a seller to record payment status separately from the order status. |
| FR-S10 | The system shall allow a seller to update delivery status, courier name, and tracking number. |
| FR-S11 | The system shall alert a seller when a product's stock is low. |
| FR-S12 | The system shall display daily and monthly sales reports and best-selling products. |
| FR-S13 | The system shall prevent a seller from viewing or changing another seller's data. |

### 3.3 Administrator Requirements

| ID | Requirement |
|---|---|
| FR-A1 | The system shall allow administrators to manage user and seller accounts (activate or deactivate). |
| FR-A2 | The system shall allow administrators to manage shops and product categories. |
| FR-A3 | The system shall allow administrators to review and remove inappropriate shops, products, or reviews. |
| FR-A4 | The system shall allow administrators to monitor platform activity. |

### 3.4 AI-Assisted Requirements

| ID | Requirement |
|---|---|
| FR-AI1 | The system shall allow sellers to generate a draft product description using AI, which the seller may edit before saving. |
| FR-AI2 | The system shall help customers discover products and shops by interest, using keyword search first and AI-assisted interpretation as an optional enhancement. |
| FR-AI3 | All core system functions shall continue to work if the AI service is unavailable. |

## 4. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-1 | Security | The system shall store passwords using Django's secure password hashing and shall never store payment PINs or card credentials. |
| NFR-2 | Security | The system shall enforce role-based access control on the server side, not only in the user interface. |
| NFR-3 | Security | The system shall use CSRF protection on all forms and shall keep secret keys in environment variables. |
| NFR-4 | Performance | Common pages, such as the home page, search results, and product pages, shall load within 3 seconds under normal usage. |
| NFR-5 | Performance | Product lists and order lists shall use pagination to avoid loading large amounts of data at once. |
| NFR-6 | Usability | The interface shall be responsive and usable on mobile phones, tablets, and desktop computers. |
| NFR-7 | Usability | The system shall display clear error and success messages for user actions. |
| NFR-8 | Reliability | Order creation shall use database transactions so that an order is either fully saved or not saved at all. |
| NFR-9 | Reliability | The system shall continue to work normally if the AI service is unavailable. |
| NFR-10 | Data Integrity | The system shall calculate prices, stock, delivery charges, and totals on the server, and shall store the product price at the time of purchase in each order item. |
| NFR-11 | Maintainability | The system shall be organized into separate Django apps, each with one clear responsibility. |
| NFR-12 | Maintainability | The source code shall be managed with Git and documented in a README file. |
| NFR-13 | Testability | Each major function shall have at least one documented test case. |
| NFR-14 | Portability | The system shall run on Windows and Linux and shall be deployable with PostgreSQL. |
