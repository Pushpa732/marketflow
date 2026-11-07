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