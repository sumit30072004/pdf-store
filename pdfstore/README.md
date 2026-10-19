# MORE POSITIONS MORE PLEASURE - two-plan store with PayU checkout

## READ THIS FIRST: PayU's policy
PayU publishes a "Banned & Restricted Category" list (https://payu.in/BannedRestrictedCategorylist).
It bans "Adult goods and services which includes pornography and other sexually suggestive
materials (includes literature, imagery, and other media)". A sex-positions guide is
very likely to be judged as falling under that.

- You can build and TEST everything with PayU test keys today. Test mode needs no approval.
- Before going live, ask PayU in writing and describe your product honestly. Get a written answer.
- NEVER register under a different business category to get approved. That is misrepresentation:
  accounts get closed and settlements held, and customer money can be frozen.
- If PayU says no, use a gateway whose written policy allows your product, or take payments
  directly by UPI. Do not guess; read each provider's prohibited-business list first.

## Plans
| Plan | Price | Unlocks |
|------|-------|---------|
| Basic Plan | Rs 49 | `BASIC_PDF_FILE` (10 positions) |
| Premium Plan | Rs 149 | `PREMIUM_PDF_FILE` (100 positions) |

## How a payment flows
1. Customer picks a plan and enters name, email, mobile, 18+ tick.
2. Your server creates an order (txnid + the plan's price) and signs it with your Salt (SHA-512).
3. The customer's browser is posted to PayU. PayU shows UPI / cards / net banking.
4. PayU posts the result back to `/payu/return` AND calls `/payu/webhook` (server to server).
5. Your server recomputes PayU's response hash and checks the amount equals the plan price.
   Only then is the order `paid` and the **Download PDF** button shown.
6. Anything unverified stays `created`; the admin page has "Check with PayU" (Verify Payment API).

## Step-by-step: PayU TEST mode (learn it safely)
1. Create a PayU merchant account at https://payu.in (business sign-up).
2. In the dashboard find **Access Test Merchant Key and Salt** (test mode) and copy both.
3. Run the site locally:
   ```
   pip install -r requirements.txt
   cp .env.example .env
   ```
   Edit `.env`:
   ```
   PAYU_KEY=your-TEST-key
   PAYU_SALT=your-TEST-salt
   PAYU_ENV=test
   DEMO_MODE=0
   ```
4. PayU must reach your site to send the result, and `surl`/`furl` must be public HTTPS.
   For local testing use a tunnel, e.g. `cloudflared tunnel --url http://localhost:5000`
   (or ngrok), then set `BASE_URL=https://<the-tunnel-address>` in `.env`.
5. `python app.py`, open the BASE_URL address, buy a plan, and pay with the test card/UPI details
   shown in PayU's docs (https://docs.payu.in) - no real money moves in test mode.
6. Confirm: the order shows **paid** in `/admin`, and the Download PDF button works.
7. Test a failed payment too, and a paid order's "Find my order" page.

## Step-by-step: going LIVE (only after PayU approves your business)
1. Complete PayU KYC and get written approval for your product category.
2. Switch the dashboard to Live mode: **Developer Tools -> API Keys** shows your live Key and Salt.
3. Deploy the site on a host with HTTPS (Render, Railway, a VPS, PythonAnywhere):
   `gunicorn app:app`, keep `orders.db` and `private/` on a persistent disk.
4. Set `.env` on the server: live `PAYU_KEY`/`PAYU_SALT`, `PAYU_ENV=live`,
   `BASE_URL=https://yourdomain.com`, `DEMO_MODE=0`, a strong `ADMIN_PASSWORD` and `SECRET_KEY`.
5. In the PayU dashboard (Developers -> Webhooks) add `https://yourdomain.com/payu/webhook` for
   SuccessfulPayment and FailedPayment. Webhooks are the most reliable signal because they work
   even if the customer closes the browser. (Menu names can change; PayU docs: /docs/webhooks)
6. Make one real Rs 49 payment yourself, check `/admin`, download the PDF, then refund it.
7. Add Privacy Policy, Terms, Refund/Cancellation and Contact pages. PayU asks for these.

## Security rules already built in (do not remove)
- Order price comes from the server's plan table, never from the browser.
- Response hash + amount are verified before an order is marked paid.
- A "failed" message can never undo a paid order.
- PDFs live in `private/` and are only served through a per-order token (limited downloads).
- Demo endpoints return 404 when `DEMO_MODE=0`.

## Files
- `.env`: prices, PDF paths, PayU keys, URLs. Never share it or commit it.
- `app.py`: `PLANS` block holds the plan descriptions.
- `private/basic-guide.pdf` (10 positions) and `private/premium-guide.pdf` (100 positions): the two guides, written for this store.
- `guide_source/`: the text and layout of both guides. Edit `content_part1-3.py`, then run `python guide_source/build_guides.py`
  to rebuild the PDFs. To use your own PDFs instead, put them in `private/` and set `BASIC_PDF_FILE` / `PREMIUM_PDF_FILE` in `.env`.

## Content rules
Only sell content you own or have rights to, keep the 18+ confirmation, and do not use pirated books.
