# ER Diagram: MarketFlow

This diagram shows the database tables that exist in the current version of the system.

```mermaid
erDiagram
    USER ||--o| SHOP : owns
    USER ||--o{ ADDRESS : saves
    USER ||--o{ ORDER : places
    SHOP ||--o{ PRODUCT : sells
    SHOP ||--o{ ORDER : receives
    CATEGORY ||--o{ PRODUCT : groups
    CATEGORY ||--o{ CATEGORY : "parent of"
    PRODUCT ||--o{ PRODUCT_IMAGE : has
    PRODUCT |o--o{ ORDER_ITEM : "sold as"
    ORDER ||--|{ ORDER_ITEM : contains
    ORDER ||--o| PAYMENT : has

    USER {
        int id PK
        string username
        string password
        string email
        string role
        string phone
    }
    SHOP {
        int id PK
        int owner_id FK
        string name
        string slug
        string logo
        text description
        string category
        string contact_phone
        string contact_email
        boolean is_published
        decimal delivery_charge
        string bkash_number
        string nagad_number
        datetime created_at
    }
    CATEGORY {
        int id PK
        int parent_id FK
        string name
        string slug
    }
    PRODUCT {
        int id PK
        int shop_id FK
        int category_id FK
        string name
        string slug
        text description
        decimal price
        int stock
        int low_stock_threshold
        boolean is_published
        datetime created_at
        datetime updated_at
    }
    PRODUCT_IMAGE {
        int id PK
        int product_id FK
        string image
        datetime created_at
    }
    ADDRESS {
        int id PK
        int user_id FK
        string full_name
        string phone
        string address_line
        string city
        boolean is_default
        datetime created_at
    }
    ORDER {
        int id PK
        string order_number
        int customer_id FK
        int shop_id FK
        string status
        decimal subtotal
        decimal delivery_charge
        decimal total
        string shipping_name
        string shipping_phone
        string shipping_address
        string shipping_city
        datetime created_at
        datetime updated_at
    }
    ORDER_ITEM {
        int id PK
        int order_id FK
        int product_id FK
        string product_name
        decimal unit_price
        int quantity
    }
    PAYMENT {
        int id PK
        int order_id FK
        string method
        string status
        decimal amount
        string transaction_id
        datetime paid_at
        datetime created_at
        datetime updated_at
    }
```

## Planned Tables

These tables belong to later phases and do not exist yet.

```mermaid
erDiagram
    ORDER ||--o| DELIVERY : has
    ORDER_ITEM ||--o| REVIEW : "reviewed in"
    USER ||--o{ REVIEW : writes
    SHOP ||--o{ REVIEW : receives

    DELIVERY {
        int id PK
        int order_id FK
        string courier
        string tracking_number
        string status
        datetime updated_at
    }
    REVIEW {
        int id PK
        int order_item_id FK
        int customer_id FK
        int shop_id FK
        int rating
        text comment
        datetime created_at
    }
```

## Design Notes

| Topic | Decision |
|---|---|
| Shopping cart | Stored in the visitor's session, not in a table, so customers can shop before logging in |
| Order snapshots | OrderItem keeps the product name and unit price; Order keeps the delivery charge, totals, and shipping details. Old orders never change when prices or addresses change. |
| One order per shop | A cart with items from several shops creates one Order (with its own Payment) for each shop |
| Separate statuses | Order status, payment status, and (planned) delivery status are stored separately |
| Protected records | A customer or shop that has orders cannot be deleted (PROTECT) |
| Product links | OrderItem.product is set to empty if a product is deleted; the copied name and price remain |
| Payment | One Payment per Order. A transaction ID can be used only once per method. |