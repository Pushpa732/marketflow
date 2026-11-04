
# MarketFlow

### Multi-Vendor E-Commerce and Business Management Software System

MarketFlow is a customer-focused multi-vendor marketplace and business management system developed using Python and Django. It enables customers to discover products from multiple shops while providing business owners with tools to manage products, inventory, orders, deliveries, payment records, and sales reports.

The project applies Software Engineering principles throughout the development process, including requirement analysis, system design, database modeling, implementation, testing, and deployment.

## Project Objectives

- Develop a centralized marketplace for multiple businesses.
- Help customers discover products and compare shops.
- Provide sellers with an integrated shop and order management dashboard.
- Support inventory tracking, delivery updates, and payment records.
- Generate sales reports and business insights.
- Integrate selected AI-assisted features.
- Build a secure, maintainable, and scalable software system.

## Key Features

### Customer Module
- Browse shops and products without signing in.
- Search products by name, category, or interest.
- Filter and sort product listings.
- View product details, shop ratings, and reviews.
- Add products to a shopping cart.
- Place orders with delivery information.
- View order history and track order status.
- Submit reviews for eligible delivered orders.

### Business Owner Module
- Register and manage a shop profile.
- Add, edit, and manage products.
- Upload product images and manage stock.
- Import products using CSV/Excel files.
- View and process incoming orders.
- Update order and delivery statuses.
- Record payment methods and payment statuses.
- Manage customer and order information.
- View sales reports and dashboard summaries.
- Receive low-stock alerts and product insights.

### Administrator Module
- Manage users and business accounts.
- Manage shops and product categories.
- Monitor platform activity.
- Review reported content.

### AI-Assisted Features
- AI-generated product descriptions.
- Product discovery and recommendation assistance.
- Basic sales insights and inventory suggestions.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Django |
| Frontend | HTML, CSS, Bootstrap, JavaScript |
| Template Engine | Django Templates |
| Database | SQLite for development |
| Data Visualization | Chart.js |
| Version Control | Git, GitHub |
| AI Integration | Selected AI API or local model |

## System Users

1. **Customers** — Discover products and place orders.
2. **Business Owners** — Manage shops, products, orders, and business operations.
3. **Administrators** — Oversee users, shops, and platform activities.

## Project Workflow

1. Business owners register and create their shops.
2. Sellers add products manually or import product data.
3. Customers browse and search the marketplace.
4. Customers add products to their cart and complete checkout.
5. Orders appear in the relevant seller dashboard.
6. Sellers process orders and update delivery information.
7. Customers track their orders.
8. Sellers monitor inventory, payments, and sales reports.

## Project Structure

```text
marketflow/
├── manage.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/
├── shops/
├── products/
├── marketplace/
├── cart/
├── orders/
├── payments/
├── reports/
├── ai_assistant/
├── templates/
├── static/
├── media/
├── requirements.txt
├── .env.example
└── README.md
```

*The structure may evolve during implementation.*

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/marketflow.git
cd marketflow
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Create an administrator account

```bash
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

Open the application at:

```text
http://127.0.0.1:8000/
```

## Project Status

**Status:** In Development

This project is being developed as a Software Engineering practicum project with a planned 60-day development timeline.

## Future Enhancements

- Official social media catalogue integration where supported.
- Online payment gateway integration.
- Advanced AI-powered recommendations.
- Real-time notifications.
- Courier service API integration.
- Mobile application.
- Advanced analytics and reporting.

## Author

**Sadia Tarannum Pushpa**  
Computer Science and Engineering  
IUBAT — International University of Business Agriculture and Technology

## License

This project is developed for academic and learning purposes. A license may be added before public distribution.
```
