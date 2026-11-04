# Use-Case Diagram: MarketFlow

```mermaid
flowchart LR
    Customer(("Customer"))
    Seller(("Seller"))
    Admin(("Administrator"))

    subgraph SYS["MarketFlow System"]
        UC1(["Register / Log in"])
        UC2(["Browse and search products"])
        UC3(["Manage shopping cart"])
        UC4(["Place order"])
        UC5(["Track orders"])
        UC6(["Write review"])
        UC7(["Use AI shopping assistant"])
        UC8(["Manage shop profile"])
        UC9(["Manage products"])
        UC10(["Import products from CSV"])
        UC11(["Manage orders"])
        UC12(["Update payment and delivery status"])
        UC13(["View sales reports"])
        UC14(["Generate AI product description"])
        UC15(["Manage users"])
        UC16(["Manage shops and categories"])
        UC17(["Review reported content"])
    end

    Customer --- UC1
    Customer --- UC2
    Customer --- UC3
    Customer --- UC4
    Customer --- UC5
    Customer --- UC6
    Customer --- UC7

    Seller --- UC1
    Seller --- UC8
    Seller --- UC9
    Seller --- UC10
    Seller --- UC11
    Seller --- UC12
    Seller --- UC13
    Seller --- UC14

    Admin --- UC1
    Admin --- UC15
    Admin --- UC16
    Admin --- UC17
```

## Actor Descriptions

| Actor | Description |
|---|---|
| Customer | Browses products, places orders, tracks deliveries, and writes reviews |
| Seller | Manages one shop, its products, orders, and sales reports |
| Administrator | Manages users, shops, categories, and reported content |