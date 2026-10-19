import os, re, json, sqlite3, secrets, hashlib, hmac
import urllib.request, urllib.parse
from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, g, abort, send_file)
from dotenv import load_dotenv

load_dotenv()
BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "orders.db")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(16))

# ---------------- settings (edit in .env) ----------------
PRODUCT_NAME = os.getenv("PRODUCT_NAME", "MORE POSITIONS MORE PLEASURE")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me")
MAX_DOWNLOADS = int(os.getenv("MAX_DOWNLOADS", "5"))

PAYU_KEY = os.getenv("PAYU_KEY", "").strip()
PAYU_SALT = os.getenv("PAYU_SALT", "").strip()
PAYU_ENV = os.getenv("PAYU_ENV", "test").strip().lower()   # test | live
DEMO_MODE = os.getenv("DEMO_MODE", "0").strip() == "1"     # fake gateway, NEVER use in production
BASE_URL = os.getenv("BASE_URL", "").strip().rstrip("/")   # public https URL of your site
PAYU_SERVICE_PROVIDER = os.getenv("PAYU_SERVICE_PROVIDER", "").strip()  # leave empty unless PayU tells you to set it

if PAYU_ENV == "live":
    PAYU_PAY_URL = "https://secure.payu.in/_payment"
    PAYU_API_URL = "https://info.payu.in/merchant/postservice.php?form=2"
else:
    PAYU_PAY_URL = "https://test.payu.in/_payment"
    PAYU_API_URL = "https://test.payu.in/merchant/postservice.php?form=2"

# ---------------- plans ----------------
# Same six rows in both plans so buyers can compare them side by side.
PLANS = {
    "basic": {
        "name": "Basic Plan",
        "price": os.getenv("BASIC_PRICE", "49"),
        "pdf": os.getenv("BASIC_PDF_FILE", "private/basic-guide.pdf"),
        "tagline": "10 good & unique positions to get you started",
        "features": [
            "10 good & unique positions",
            "Clear, step-by-step pages",
            "Beginner-friendly tips for comfort & connection",
            "A perfect starter pack for couples",
            "Instant PDF download after payment",
        ],
    },
    "premium": {
        "name": "Premium Plan",
        "price": os.getenv("PREMIUM_PRICE", "149"),
        "pdf": os.getenv("PREMIUM_PDF_FILE", "private/premium-guide.pdf"),
        "tagline": "100 exclusive & unique positions for every mood",
        "features": [
            "100 exclusive & unique positions",
            "Clear, step-by-step pages for every position",
            "Tips to keep every night comfortable, fun & fresh",
            "More spicy positions \U0001F525",
            "Instant PDF download after payment",
        ],
    },
}
for _p in PLANS.values():
    _p["amount"] = f"{Decimal(_p['price']):.2f}"          # PayU wants e.g. 49.00


def plan_key(o):
    return o["plan"] if o["plan"] in PLANS else "basic"


def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")


def gateway_ready():
    return bool(PAYU_KEY and PAYU_SALT) and not DEMO_MODE


# ---------------- database ----------------
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    d = g.pop("db", None)
    if d:
        d.close()


def init_db():
    with sqlite3.connect(DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS payments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            txnid TEXT UNIQUE, name TEXT, email TEXT, phone TEXT, amount TEXT,
            plan TEXT DEFAULT 'basic',
            status TEXT DEFAULT 'created',
            mihpayid TEXT, mode TEXT, bank_ref TEXT, note TEXT,
            dl_token TEXT UNIQUE, downloads INTEGER DEFAULT 0,
            created TEXT, paid_at TEXT)""")
        cols = [r[1] for r in c.execute("PRAGMA table_info(payments)")]
        if "plan" not in cols:                             # upgrade an older database
            c.execute("ALTER TABLE payments ADD COLUMN plan TEXT DEFAULT 'basic'")


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def get_order(txnid):
    return db().execute("SELECT * FROM payments WHERE txnid=?", (txnid,)).fetchone()


def mark_paid(txnid, mihpayid="", mode="", bank_ref=""):
    o = get_order(txnid)
    if not o or o["status"] == "paid":
        return
    db().execute(
        "UPDATE payments SET status='paid', mihpayid=?, mode=?, bank_ref=?, "
        "dl_token=?, paid_at=?, note=NULL WHERE txnid=?",
        (mihpayid, mode, bank_ref, secrets.token_urlsafe(24), now(), txnid))
    db().commit()


def mark_failed(txnid, note=""):
    db().execute("UPDATE payments SET status='failed', note=? WHERE txnid=? AND status!='paid'",
                 ((note or "")[:200], txnid))
    db().commit()


# ---------------- PayU hashing / verification ----------------
def sha512(s):
    return hashlib.sha512(s.encode("utf-8")).hexdigest()


def request_hash(f):
    # key|txnid|amount|productinfo|firstname|email|udf1..udf5||||||SALT
    parts = ([PAYU_KEY, f["txnid"], f["amount"], f["productinfo"], f["firstname"], f["email"]]
             + [f.get("udf%d" % i, "") for i in range(1, 6)] + [""] * 5 + [PAYU_SALT])
    return sha512("|".join(parts))


def response_hash(d):
    # SALT|status||||||udf5|udf4|udf3|udf2|udf1|email|firstname|productinfo|amount|txnid|key
    parts = ([PAYU_SALT, d.get("status", "")] + [""] * 5
             + [d.get("udf%d" % i, "") for i in range(5, 0, -1)]
             + [d.get("email", ""), d.get("firstname", ""), d.get("productinfo", ""),
                d.get("amount", ""), d.get("txnid", ""), d.get("key", "")])
    if d.get("additionalCharges"):
        parts.insert(0, d["additionalCharges"])
    return sha512("|".join(parts))


def valid_response(d):
    if d.get("key") != PAYU_KEY:
        return False
    return hmac.compare_digest(response_hash(d).lower(), (d.get("hash") or "").lower())


def apply_payu_response(d):
    """Trust only PayU's signed response. Returns (order, error_message)."""
    o = get_order(d.get("txnid", ""))
    if not o:
        return None, "Unknown order."
    if not gateway_ready() or not valid_response(d):
        return o, "We could not verify the payment response. If money was deducted, use 'Check payment status'."
    try:
        if Decimal(d.get("amount", "0")) != Decimal(o["amount"]):
            return o, "Payment amount did not match the order."
    except InvalidOperation:
        return o, "Invalid payment amount."
    if (d.get("status") or "").lower() == "success":
        mark_paid(o["txnid"], d.get("mihpayid", ""), d.get("mode", ""), d.get("bank_ref_num", ""))
    else:
        mark_failed(o["txnid"], d.get("error_Message") or d.get("field9") or d.get("status", "failed"))
    return get_order(o["txnid"]), None


def payu_verify(txnid):
    """Ask PayU directly (server to server) what happened to this transaction."""
    cmd = "verify_payment"
    body = urllib.parse.urlencode({
        "key": PAYU_KEY, "command": cmd, "var1": txnid,
        "hash": sha512(f"{PAYU_KEY}|{cmd}|{txnid}|{PAYU_SALT}")}).encode()
    req = urllib.request.Request(PAYU_API_URL, data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=15) as r:
        j = json.loads(r.read().decode())
    t = (j.get("transaction_details") or {}).get(txnid)
    if isinstance(t, list):
        t = t[-1] if t else None
    return t


def check_with_payu(o):
    """Re-check an unpaid order with PayU. Returns a message for the user."""
    t = payu_verify(o["txnid"])
    if not t:
        return "PayU has no payment for this order yet."
    status = (t.get("status") or "").lower()
    try:
        amt_ok = Decimal(str(t.get("amt") or t.get("transaction_amount") or "0")) == Decimal(o["amount"])
    except InvalidOperation:
        amt_ok = False
    if status == "success" and amt_ok:
        mark_paid(o["txnid"], str(t.get("mihpayid", "")), t.get("mode", ""), t.get("bank_ref_num", ""))
        return "Payment confirmed. Your download is ready."
    if status in ("failure", "failed", "usercancelled", "dropped", "bounced"):
        mark_failed(o["txnid"], status)
        return "PayU reports this payment did not go through."
    return "Payment is still pending at PayU. Please check again in a minute."


# ---------------- helpers ----------------
@app.context_processor
def inject():
    return {"demo": DEMO_MODE}


def admin_required(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return f(*a, **k)
    return w


# ---------------- public pages ----------------
@app.route("/")
def index():
    return render_template("index.html", name=PRODUCT_NAME, plans=PLANS)


@app.route("/buy", methods=["GET", "POST"])
def buy():
    sel = request.values.get("plan", "basic")
    if sel not in PLANS:
        sel = "basic"
    if request.method == "POST":
        plan = request.form.get("plan", "")
        name = re.sub(r"[^A-Za-z0-9 ]", "", request.form.get("name", "")).strip()[:60]
        email = request.form.get("email", "").strip().lower()
        phone = re.sub(r"\D", "", request.form.get("phone", ""))[-10:]
        if plan not in PLANS:
            flash("Please choose a plan.")
        elif not request.form.get("age"):
            flash("You must confirm you are 18 or older.")
        elif not name:
            flash("Please enter your name (letters and numbers only).")
        elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            flash("Please enter a valid email address.")
        elif not re.fullmatch(r"[6-9]\d{9}", phone):
            flash("Please enter a valid 10-digit mobile number.")
        else:
            txnid = "MPMP" + secrets.token_hex(8)
            db().execute(
                "INSERT INTO payments(txnid,name,email,phone,amount,plan,created) VALUES(?,?,?,?,?,?,?)",
                (txnid, name, email, phone, PLANS[plan]["amount"], plan, now()))
            db().commit()
            return redirect(url_for("pay", txnid=txnid))
    return render_template("buy.html", name=PRODUCT_NAME, plans=PLANS, sel=sel)


@app.route("/pay/<txnid>")
def pay(txnid):
    o = get_order(txnid) or abort(404)
    plan = PLANS[plan_key(o)]
    if o["status"] == "paid":
        return redirect(url_for("order", txnid=txnid))
    if DEMO_MODE:
        return render_template("demo_gateway.html", o=o, plan=plan)
    if not gateway_ready():
        return "Payment gateway is not configured yet.", 503
    root = BASE_URL or request.url_root.rstrip("/")
    ret = root + url_for("payu_return")
    f = {
        "key": PAYU_KEY, "txnid": o["txnid"], "amount": o["amount"],
        "productinfo": re.sub(r"[^A-Za-z0-9 ]", "", f"{PRODUCT_NAME} {plan['name']}")[:100],
        "firstname": o["name"], "email": o["email"], "phone": o["phone"],
        "surl": ret, "furl": ret,
    }
    if PAYU_SERVICE_PROVIDER:
        f["service_provider"] = PAYU_SERVICE_PROVIDER
    f["hash"] = request_hash(f)
    return render_template("payu_redirect.html", action=PAYU_PAY_URL, fields=f)


@app.route("/payu/return", methods=["GET", "POST"])
def payu_return():
    """PayU sends the customer's browser here (success and failure)."""
    if request.method == "GET":
        return redirect(url_for("index"))
    o, err = apply_payu_response(request.form.to_dict())
    if err:
        flash(err)
    if not o:
        return redirect(url_for("index"))
    return redirect(url_for("order", txnid=o["txnid"]))


@app.route("/payu/webhook", methods=["POST"])
def payu_webhook():
    """Server-to-server notification from PayU (set this URL in the PayU dashboard)."""
    data = request.form.to_dict() or (request.get_json(silent=True) or {})
    apply_payu_response({k: str(v) for k, v in data.items()})
    return "OK", 200


@app.route("/order/<txnid>")
def order(txnid):
    o = get_order(txnid) or abort(404)
    left = max(MAX_DOWNLOADS - (o["downloads"] or 0), 0)
    return render_template("order.html", o=o, plan=PLANS[plan_key(o)], left=left,
                           max_dl=MAX_DOWNLOADS, can_check=gateway_ready())


@app.route("/order/<txnid>/check", methods=["POST"])
def order_check(txnid):
    o = get_order(txnid) or abort(404)
    if not gateway_ready():
        abort(404)
    try:
        flash(check_with_payu(o))
    except Exception:
        flash("Could not reach PayU right now. Please try again in a minute.")
    return redirect(url_for("order", txnid=txnid))


@app.route("/download/<token>")
def download(token):
    o = db().execute("SELECT * FROM payments WHERE dl_token=? AND status='paid'",
                     (token,)).fetchone() or abort(404)
    if (o["downloads"] or 0) >= MAX_DOWNLOADS:
        flash("Download limit reached. Please contact support with your Order ID.")
        return redirect(url_for("order", txnid=o["txnid"]))
    plan = PLANS[plan_key(o)]
    path = os.path.join(BASE, plan["pdf"])
    if not os.path.exists(path):
        return "The file is temporarily unavailable. Please contact support.", 500
    db().execute("UPDATE payments SET downloads=downloads+1 WHERE id=?", (o["id"],))
    db().commit()
    return send_file(path, mimetype="application/pdf", as_attachment=True,
                     download_name=slug(f"{PRODUCT_NAME} {plan['name']}") + ".pdf")


@app.route("/find", methods=["GET", "POST"])
def find():
    if request.method == "POST":
        o = get_order(request.form.get("order_id", "").strip())
        if o and o["email"] == request.form.get("email", "").strip().lower():
            return redirect(url_for("order", txnid=o["txnid"]))
        flash("No order found for those details.")
    return render_template("find.html")


# ---------------- demo gateway (only when DEMO_MODE=1) ----------------
@app.route("/demo/<txnid>/<outcome>", methods=["POST"])
def demo_pay(txnid, outcome):
    if not DEMO_MODE:
        abort(404)
    get_order(txnid) or abort(404)
    if outcome == "success":
        mark_paid(txnid, "DEMO" + secrets.token_hex(4), "DEMO")
    else:
        mark_failed(txnid, "Demo: payment cancelled")
    return redirect(url_for("order", txnid=txnid))


# ---------------- admin ----------------
@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if secrets.compare_digest(request.form.get("password", ""), ADMIN_PASSWORD):
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Wrong password.")
    return render_template("login.html")


@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin():
    rows = db().execute("SELECT * FROM payments ORDER BY id DESC").fetchall()
    paid = [r for r in rows if r["status"] == "paid"]
    revenue = sum(float(r["amount"]) for r in paid)
    by_plan = {k: sum(1 for r in paid if plan_key(r) == k) for k in PLANS}
    return render_template("admin.html", rows=rows, paid_count=len(paid), revenue=revenue,
                           by_plan=by_plan, plans=PLANS, can_check=gateway_ready())


@app.route("/admin/check/<txnid>", methods=["POST"])
@admin_required
def admin_check(txnid):
    o = get_order(txnid) or abort(404)
    if gateway_ready():
        try:
            flash(f"{txnid}: {check_with_payu(o)}")
        except Exception as e:
            flash(f"Could not reach PayU: {e}")
    return redirect(url_for("admin"))


init_db()
if __name__ == "__main__":
    app.run(debug=True)
