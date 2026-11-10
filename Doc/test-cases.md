# Test Cases: Phase 2 (Accounts and Shops)

| ID | Scenario | Related Req. | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| TC-01 | Customer registers | FR-C7 | Open Register, fill the form with role Customer, submit | Account created, user logged in, success message | As expected | Pass |
| TC-02 | Seller registers | FR-S1 | Open Register, fill the form with role Seller, submit | Account created with role seller | As expected | Pass |
| TC-03 | Register as administrator | NFR-2 | Send a registration with role "admin" | Request rejected, no account created | As expected | Pass |
| TC-04 | Login with correct password | FR-C7 | Open Login, enter valid username and password | User logged in, redirected to home | As expected | Pass |
| TC-05 | Login with wrong password | NFR-1 | Enter a wrong password | Error shown, user not logged in | As expected | Pass |
| TC-06 | Visitor opens seller dashboard | NFR-2 | Open /seller/dashboard/ while logged out | Redirected to login page | As expected | Pass |
| TC-07 | Customer opens seller dashboard | NFR-2, FR-S13 | Log in as customer, open /seller/dashboard/ | "Access Denied" page (403) | As expected | Pass |
| TC-08 | Seller creates shop profile | FR-S2 | Log in as seller, open Create your shop, save | Shop saved with automatic slug | As expected | Pass |
| TC-09 | Seller data isolation | FR-S13 | Log in as a second seller, open Dashboard | Only own shop shown, never another seller's | As expected | Pass |
| TC-10 | Publish without description | FR-S2 | Click Publish on a shop with no description | Error message, shop stays Draft | As expected | Pass |
| TC-11 | Publish shop | FR-S2 | Click Publish on a complete shop | Shop appears on the home page | As expected | Pass |
| TC-12 | Unpublish shop | FR-S2 | Click Unpublish | Shop disappears from the home page | As expected | Pass |

## Phase 3: Catalog (Products and Images)

| ID | Scenario | Related Req. | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| TC-13 | Seller adds a product | FR-S3 | Open Add product, fill the form, save | Product saved under the seller's own shop | As expected | Pass |
| TC-14 | Price of zero | NFR-10 | Add a product with price 0 | Error shown, nothing saved | As expected | Pass |
| TC-15 | Seller edits own product | FR-S3 | Click Edit, change the price, save | New price saved and shown in list | As expected | Pass |
| TC-16 | Seller deletes own product | FR-S3 | Click Delete, then confirm | Confirmation page first, then product removed | As expected | Pass |
| TC-17 | Edit another seller's product | FR-S13 | Open another seller's product edit address | 404 Not Found, data unchanged | As expected | Pass |
| TC-18 | Customer opens product pages | NFR-2 | Log in as customer, open /seller/products/ | Access Denied (403) | As expected | Pass |
| TC-19 | Upload a valid image | FR-S4 | Open Images, upload a JPG or PNG | Image saved and shown as Main | As expected | Pass |
| TC-20 | Upload a non-image file | FR-S4 | Upload a .txt file | Error shown, nothing saved | As expected | Pass |
| TC-21 | Upload more than 5 images | FR-S4 | Upload a 6th image | Upload blocked with a message | As expected | Pass |
| TC-22 | Low-stock alert | FR-S11 | Add a product with stock below its alert level | Red "Low stock" badge in the list | As expected | Pass |

## Phase 3: CSV Import

| ID | Scenario | Related Req. | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| TC-23 | Download CSV template | FR-S5 | Open Import CSV, click Download CSV template | File with header and two example rows downloads | As expected | Pass |
| TC-24 | Import a valid CSV | FR-S5 | Upload a correct file | Products saved as drafts in the seller's own shop, success message | As expected | Pass |
| TC-25 | Upload a non-CSV file | FR-S5 | Upload a .txt or .jpg file | Error: only .csv files accepted | As expected | Pass |
| TC-26 | Missing required column | FR-S5 | Upload a file without the price column | Error naming the missing column | As expected | Pass |
| TC-27 | Invalid values in rows | FR-S5, NFR-10 | Upload rows with a bad price, bad stock, or empty name | Report listing each problem per row | As expected | Pass |
| TC-28 | Unknown category | FR-S5 | Upload a row with a category that does not exist | Row error naming the category | As expected | Pass |
| TC-29 | One bad row | FR-S5, NFR-8 | Upload a file with one good and one bad row | Nothing imported (all-or-nothing) | As expected | Pass |
| TC-30 | Duplicate product name | FR-S5 | Upload the same valid file twice | Second upload rejected, no duplicates | As expected | Pass |
| TC-31 | Import goes to own shop only | FR-S13 | Import as seller2, check seller1's products | Products appear only in seller2's shop | As expected | Pass |
| TC-32 | Customer opens import page | NFR-2 | Log in as customer, open /seller/products/import/ | Access Denied (403) | As expected | Pass |


## Phase 4: Marketplace and Search

| ID | Scenario | Related Req. | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| TC-33 | Browse without logging in | FR-C1 | Log out, open home, products, shops, a shop page, a product page | All pages open without login | As expected | Pass |
| TC-34 | Draft product is hidden | FR-C13, NFR-2 | Open a draft product's address, search for its name | 404 page, never in listings or search | As expected | Pass |
| TC-35 | Draft shop is hidden | FR-C13, NFR-2 | Open a draft shop's address, search for its name | 404 page, shop and its products never listed | As expected | Pass |
| TC-36 | Keyword search | FR-C2 | Search "shirt" (and "SHIRT") | Matching products found, capital letters ignored | As expected | Pass |
| TC-37 | Multi-word search | FR-C2 | Search "blue shirt" | Products containing all words found | As expected | Pass |
| TC-38 | Search by shop or category | FR-C2 | Search a shop name, then a category name | Shop, its products, or category link shown | As expected | Pass |
| TC-39 | Search with no result | FR-C2 | Search "zzzz" | Friendly "No results" message | As expected | Pass |
| TC-40 | Unsafe search text | NFR-1, NFR-3 | Search `<script>alert(1)</script>` and `' OR 1=1 --` | Shown as plain text, no popup, no error | As expected | Pass |
| TC-41 | Filter by category | FR-C3 | Choose a category and click Apply | Only products of that category | As expected | Pass |
| TC-42 | Filter by price range | FR-C3 | Set min 400 and max 500 | Only products priced in that range | As expected | Pass |
| TC-43 | Combined filters | FR-C3 | Combine category, shop, and price | Only products matching all filters | As expected | Pass |
| TC-44 | Invalid filter input | NFR-7 | Minimum above maximum, text as price, unknown shop in address | Clear error message, no crash page | As expected | Pass |
| TC-45 | Sorting | FR-C3 | Choose each sort option | Products in the correct order | As expected | Pass |
| TC-46 | Pagination keeps choices | NFR-5 | Sort, then go to page 2 | Sort and filters stay on page 2 | As expected | Pass |
| TC-47 | Friendly 404 page | NFR-7 | Open a page that does not exist (with DEBUG off) | Friendly 404 page with buttons | As expected | Pass |

## Phase 5: Shopping Cart

| ID | Scenario | Related Req. | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| TC-48 | Add to cart without logging in | FR-C6 | Log out, open a product, click Add to cart | Item appears in the cart, navbar count updates | As expected | Pass |
| TC-49 | Add the same product twice | FR-C6 | Add a product, then add it again | Quantity increases, no duplicate line | As expected | Pass |
| TC-50 | Cart with two shops | FR-C6, FR-C10 | Add products from two shops | Items grouped by shop, each shop has a subtotal, total is correct | As expected | Pass |
| TC-51 | Update and remove | FR-C6 | Change a quantity, set 0, click Remove | Totals update, items disappear | As expected | Pass |
| TC-52 | Quantity above stock | NFR-10 | Add more than the stock | Quantity limited to stock, warning shown | As expected | Pass |
| TC-53 | Unavailable product | FR-C13 | Try to add an out-of-stock, draft, or draft-shop product | Not added (message or 404) | As expected | Pass |
| TC-54 | Invalid quantity | NFR-7 | Send abc, -3, 0, or 1000 as quantity | Rejected with a clear message | As expected | Pass |
| TC-55 | Price tampering | NFR-10 | Send a fake price with the add request | Fake price ignored, real price used | As expected | Pass |
| TC-56 | Product changes after adding | NFR-10 | Seller unpublishes, changes price, or sells out a product in a cart | Cart shows current data and explains any removal | As expected | Pass |
| TC-57 | Login keeps the cart | FR-C7 | Fill the cart as a visitor, then log in | Cart is still there | As expected | Pass |
| TC-58 | Cart privacy | NFR-2 | Open the cart in a second browser | Second visitor sees an empty cart | As expected | Pass |

## Phase 5: Delivery Addresses

| ID | Scenario | Related Req. | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| TC-59 | Customer adds an address | FR-C8 | Log in as customer, open My addresses, add an address | Address saved, shown in the list | As expected | Pass |
| TC-60 | First address is default | FR-C8 | Add the first address, then a second | First is default, second is not | As expected | Pass |
| TC-61 | Change the default | FR-C8 | Tick default on a new address, or click Make default | Only one address is default | As expected | Pass |
| TC-62 | Invalid phone number | FR-C8, NFR-7 | Save an address with phone 12345 | Clear error, nothing saved | As expected | Pass |
| TC-63 | Edit and delete own address | FR-C8 | Edit, then delete an address | Changes saved, deletion needs confirmation | As expected | Pass |
| TC-64 | Address limit | NFR-7 | Try to add a sixth address | Blocked with a message | As expected | Pass |
| TC-65 | Another customer's address | FR-C13 | Open another customer's address edit or delete address | 404 Not Found, data unchanged | As expected | Pass |
| TC-66 | Seller opens address pages | NFR-2 | Log in as seller, open /my/addresses/ | Access Denied (403) | As expected | Pass |
| TC-67 | Visitor opens address pages | NFR-2 | Log out, open /my/addresses/ | Redirected to login | As expected | Pass |

## Phase 5: Checkout Page and Delivery Charges

| ID | Scenario | Related Req. | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| TC-68 | Visitor goes to checkout | FR-C7 | Log out, fill the cart, click Proceed to checkout | Redirected to login, then back to checkout with the cart intact | As expected | Pass |
| TC-69 | Seller opens checkout | NFR-2 | Log in as seller, open /checkout/ | Redirected to cart with a message | As expected | Pass |
| TC-70 | Checkout with empty cart | NFR-7 | Open /checkout/ with an empty cart | Redirected to cart with a message | As expected | Pass |
| TC-71 | Delivery charge per shop | FR-C10, NFR-10 | Order from two shops with different charges | Each shop shows its own delivery charge and total, grand total is correct | As expected | Pass |
| TC-72 | Free delivery | NFR-10 | Seller sets charge 0 | Delivery shown as Free | As expected | Pass |
| TC-73 | Seller delivery charge validation | NFR-7 | Enter -5, 5001, or text as charge | Rejected with an error | As expected | Pass |
| TC-74 | Address selection | FR-C8 | Open checkout with several saved addresses | Default address preselected, others selectable | As expected | Pass |
| TC-75 | Another customer's address | FR-C13 | Add ?address= with another customer's address number | Ignored, default used, address never shown | As expected | Pass |
| TC-76 | No saved address | FR-C8 | Open checkout without an address | Prompt to add one, then return to checkout | As expected | Pass |
| TC-77 | Unsafe return address | NFR-3 | Open Add address with ?next=https://evil.example/ and save | Ignored, user stays on this website | As expected | Pass |