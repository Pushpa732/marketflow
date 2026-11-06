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