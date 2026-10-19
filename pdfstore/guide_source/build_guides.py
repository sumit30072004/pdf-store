"""Builds the two PDF guides (Basic = 10 positions, Premium = 100 positions).

Run:  python guide_source/build_guides.py
Output: private/basic-guide.pdf and private/premium-guide.pdf
"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit, ImageReader
from reportlab.lib.colors import HexColor, Color

from content_part1 import CH1, CH2, CH3
from content_part2 import CH4, CH5
from content_part3 import CH6, CH7, CH8, BASIC_NAMES, RULES, TIPS

CHAPTERS = [CH1, CH2, CH3, CH4, CH5, CH6, CH7, CH8]
BRAND = "MORE POSITIONS MORE PLEASURE"
YEAR = "2026"

for name, f in [("P", "Poppins-Regular"), ("PM", "Poppins-Medium"), ("PB", "Poppins-Bold"),
                ("PI", "Poppins-Italic"), ("PL", "Poppins-Light")]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(HERE, "fonts", f + ".ttf")))

W, H = A5
PLUM = HexColor("#2a1636")
PLUM2 = HexColor("#4a2a5e")
CREAM = HexColor("#fbf5ee")
INK = HexColor("#3a2548")
MUTED = HexColor("#85748f")
PINK = HexColor("#e0457b")
GOLD = HexColor("#f0a35e")
LINE = HexColor("#eadfe9")
CHAPTER_COLORS = ["#e0457b", "#ef6a5b", "#d98a1f", "#b44fa0", "#d1456a", "#c65d3b", "#8f4bc4", "#e8392f"]

CARD_W, CARD_H = W - 60, 232
CARD_X = 30


def mix(c1, c2, t):
    return Color(c1.red + (c2.red - c1.red) * t, c1.green + (c2.green - c1.green) * t,
                 c1.blue + (c2.blue - c1.blue) * t)


def flame(c, cx, y, s, color, inner=None):
    """Draws a simple flame icon, bottom centre at (cx, y), height s."""
    def shape(sc, dy, col):
        p = c.beginPath()
        x, yy = cx, y + dy
        p.moveTo(x, yy)
        p.curveTo(x - 0.40 * sc, yy + 0.00 * sc, x - 0.42 * sc, yy + 0.38 * sc, x - 0.20 * sc, yy + 0.58 * sc)
        p.curveTo(x - 0.17 * sc, yy + 0.46 * sc, x - 0.11 * sc, yy + 0.40 * sc, x - 0.04 * sc, yy + 0.36 * sc)
        p.curveTo(x - 0.10 * sc, yy + 0.64 * sc, x + 0.00 * sc, yy + 0.84 * sc, x + 0.12 * sc, yy + 1.00 * sc)
        p.curveTo(x + 0.34 * sc, yy + 0.80 * sc, x + 0.44 * sc, yy + 0.50 * sc, x + 0.38 * sc, yy + 0.30 * sc)
        p.curveTo(x + 0.35 * sc, yy + 0.10 * sc, x + 0.20 * sc, yy + 0.00 * sc, x, yy)
        p.close()
        c.setFillColor(col)
        c.drawPath(p, stroke=0, fill=1)
    shape(s, 0, color)
    shape(s * 0.5, s * 0.04, inner or GOLD)


def para(c, text, x, y, width, font, size, leading, color):
    c.setFillColor(color)
    c.setFont(font, size)
    for line in simpleSplit(text, font, size, width):
        c.drawString(x, y, line)
        y -= leading
    return y


def centered(c, text, cx, y, font, size, color):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawCentredString(cx, y, text)


def gradient_text(c, text, cx, y, font, size, c1, c2):
    total = pdfmetrics.stringWidth(text, font, size)
    x = cx - total / 2
    n = max(len(text) - 1, 1)
    c.setFont(font, size)
    for i, ch in enumerate(text):
        c.setFillColor(mix(c1, c2, i / n))
        c.drawString(x, y, ch)
        x += pdfmetrics.stringWidth(ch, font, size)


def fit_size(text, font, target_w, max_size):
    return min(max_size, max_size * target_w / pdfmetrics.stringWidth(text, font, max_size))


def pill(c, cx, y, text, font, size, fill, fg, padx=12, h=20):
    w = pdfmetrics.stringWidth(text, font, size) + 2 * padx
    c.setFillColor(fill)
    c.roundRect(cx - w / 2, y, w, h, h / 2, stroke=0, fill=1)
    c.setFillColor(fg)
    c.setFont(font, size)
    c.drawCentredString(cx, y + (h - size) / 2 + size * 0.18, text)


def glow(c, cx, cy, r, color, steps=26, alpha=0.05):
    for i in range(steps):
        rr = r * (1 - i / steps)
        c.setFillColor(color)
        c.setFillAlpha(alpha)
        c.circle(cx, cy, rr, stroke=0, fill=1)
    c.setFillAlpha(1)


# ------------------------------------------------------------------ pages
def page_cover(c, ctx):
    c.setFillColor(PLUM); c.rect(0, 0, W, H, stroke=0, fill=1)
    glow(c, W / 2, H * 0.52, 250, PINK, alpha=0.035)
    c.setStrokeColor(PINK); c.setLineWidth(0.8)
    for i, r in enumerate([120, 160, 200, 240, 280]):
        c.setStrokeAlpha(0.25 - i * 0.04)
        c.circle(W / 2, H * 0.52, r, stroke=1, fill=0)
    c.setStrokeAlpha(1)
    pill(c, W / 2, H - 58, "18+  ONLY", "PB", 8.5, PINK, HexColor("#ffffff"), padx=14, h=20)
    flame(c, W / 2, H - 205, 100, PINK, GOLD)
    s = fit_size("MORE POSITIONS", "PB", W - 70, 38)
    gradient_text(c, "MORE POSITIONS", W / 2, H - 258, "PB", s, PINK, GOLD)
    s2 = fit_size("MORE PLEASURE", "PB", W - 90, 38)
    gradient_text(c, "MORE PLEASURE", W / 2, H - 258 - s * 1.15, "PB", s, GOLD, PINK)
    c.setStrokeColor(GOLD); c.setLineWidth(1.4)
    c.line(W / 2 - 40, H - 330, W / 2 + 40, H - 330)
    centered(c, ctx["plan"].upper(), W / 2, H - 372, "PB", 20, HexColor("#ffffff"))
    centered(c, ctx["sub"], W / 2, H - 395, "PL", 12, HexColor("#e9d9ee"))
    centered(c, "A guide for couples: closeness, comfort and confidence", W / 2, 120, "PI", 9, HexColor("#cdb6d6"))
    centered(c, "For adults 18+ only. Personal use only.", W / 2, 56, "PL", 8, HexColor("#a58bb3"))


def inner_bg(c, ctx, right):
    c.setFillColor(CREAM); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(MUTED); c.setFont("PM", 6.5)
    c.drawString(CARD_X, H - 30, BRAND)
    c.drawRightString(W - CARD_X, H - 30, right.upper())
    c.setStrokeColor(LINE); c.setLineWidth(0.6)
    c.line(CARD_X, H - 38, W - CARD_X, H - 38)
    c.setFillColor(MUTED); c.setFont("P", 8)
    c.drawCentredString(W / 2, 20, str(ctx["pageno"]))


def title_block(c, title, sub=None):
    c.setFillColor(INK); c.setFont("PB", 25)
    c.drawString(CARD_X, H - 82, title)
    c.setFillColor(PINK); c.rect(CARD_X, H - 94, 44, 3, stroke=0, fill=1)
    if sub:
        para(c, sub, CARD_X, H - 114, W - 2 * CARD_X, "PI", 10, 15, MUTED)


def page_welcome(c, ctx):
    inner_bg(c, ctx, "Welcome")
    title_block(c, "Welcome")
    flame(c, W - 62, H - 98, 36, PINK, GOLD)
    y = H - 130
    texts = [
        "This guide is for consenting adults aged 18 and over. It is written to help couples explore closeness, communication and comfort together, one position at a time.",
        "Every body is different. What feels wonderful for one couple may not suit another, and that is completely fine. Treat these pages as a menu, not a checklist: pick what appeals to you, skip what doesn't, and change anything that doesn't feel right.",
        "Each position has a short how-to, a practical tip and three ratings, so you can choose by mood: relaxed, close, playful or energetic.",
        "The most important ingredient is not in any position. It is the two of you, talking openly, going at your own pace and enjoying each other.",
    ]
    for t in texts:
        y = para(c, t, CARD_X, y, W - 2 * CARD_X, "P", 10.2, 16.5, INK) - 10
    c.setFillColor(HexColor("#f5e6ee")); c.roundRect(CARD_X, 54, W - 2 * CARD_X, 78, 10, stroke=0, fill=1)
    c.setFillColor(PINK); c.rect(CARD_X, 54, 4, 78, stroke=0, fill=1)
    c.setFillColor(INK); c.setFont("PB", 9.5); c.drawString(CARD_X + 18, 112, "A note on health")
    para(c, "This guide is general education and is not medical advice. If you have pain, health concerns or questions about contraception, please speak to a doctor.",
         CARD_X + 18, 96, W - 2 * CARD_X - 34, "P", 8.8, 13, INK)


def page_rules(c, ctx):
    inner_bg(c, ctx, "The Golden Rules")
    title_block(c, "The Golden Rules")
    y = H - 118
    for i, (h, t) in enumerate(RULES, 1):
        lines = simpleSplit(t, "P", 8.8, W - 2 * CARD_X - 62)
        hh = 26 + 12.5 * len(lines)
        c.setFillColor(HexColor("#ffffff")); c.setStrokeColor(LINE)
        c.roundRect(CARD_X, y - hh, W - 2 * CARD_X, hh, 9, stroke=1, fill=1)
        c.setFillColor(PINK); c.circle(CARD_X + 20, y - 20, 11, stroke=0, fill=1)
        centered(c, str(i), CARD_X + 20, y - 24, "PB", 10.5, HexColor("#ffffff"))
        c.setFillColor(INK); c.setFont("PB", 10); c.drawString(CARD_X + 42, y - 19, h)
        para(c, t, CARD_X + 42, y - 33, W - 2 * CARD_X - 62, "P", 8.8, 12.5, INK)
        y -= hh + 9


def dots(c, x, y, n, color):
    for i in range(5):
        cx = x + i * 9.2
        if i < n:
            c.setFillColor(color); c.circle(cx, y, 3.1, stroke=0, fill=1)
        else:
            c.setStrokeColor(color); c.setLineWidth(0.7); c.setFillColor(HexColor("#ffffff"))
            c.circle(cx, y, 3.1, stroke=1, fill=1)


def page_howto(c, ctx):
    inner_bg(c, ctx, "How to use this guide")
    title_block(c, "How to Use This Guide")
    y = H - 122
    y = para(c, "Every position comes with three ratings from one to five dots.", CARD_X, y, W - 2 * CARD_X, "P", 10, 16, INK) - 8
    for label, text in [("Comfort", "How easy and relaxing the position is to hold. More dots mean less effort."),
                        ("Intimacy", "How close you are, and how much eye contact and connection there is."),
                        ("Energy", "How much effort the position takes. One dot is calm, five is a workout.")]:
        c.setFillColor(HexColor("#ffffff")); c.setStrokeColor(LINE)
        c.roundRect(CARD_X, y - 46, W - 2 * CARD_X, 46, 9, stroke=1, fill=1)
        c.setFillColor(INK); c.setFont("PB", 10); c.drawString(CARD_X + 14, y - 18, label)
        dots(c, CARD_X + 14 + 4, y - 34, 3, PINK)
        para(c, text, CARD_X + 100, y - 18, W - 2 * CARD_X - 116, "P", 8.6, 12.5, INK)
        y -= 56
    y -= 6
    c.setFillColor(INK); c.setFont("PB", 12); c.drawString(CARD_X, y, "Choose by mood"); y -= 20
    moods = ctx["moods"]
    for m, t in moods:
        c.setFillColor(PINK); c.circle(CARD_X + 4, y + 3, 2.4, stroke=0, fill=1)
        c.setFillColor(INK); c.setFont("PB", 9.2); c.drawString(CARD_X + 14, y, m)
        y = para(c, t, CARD_X + 14 + pdfmetrics.stringWidth(m, "PB", 9.2) + 6, y, W - 2 * CARD_X - 30 - pdfmetrics.stringWidth(m, "PB", 9.2),
                 "P", 9, 13, INK) - 8


def page_toc(c, ctx):
    inner_bg(c, ctx, "Contents")
    title_block(c, "Contents")
    y = H - 128
    for ci, ch in enumerate(CHAPTERS):
        col = HexColor(CHAPTER_COLORS[ci])
        c.setFillColor(col); c.roundRect(CARD_X, y - 24, 30, 30, 8, stroke=0, fill=1)
        centered(c, "%02d" % (ci + 1), CARD_X + 15, y - 14, "PB", 10.5, HexColor("#ffffff"))
        c.setFillColor(INK); c.setFont("PB", 11.5)
        title = ch["title"]
        c.drawString(CARD_X + 42, y - 8, title)
        if ch.get("spicy"):
            flame(c, CARD_X + 42 + pdfmetrics.stringWidth(title, "PB", 11.5) + 12, y - 11, 14, PINK, GOLD)
        c.setFillColor(MUTED); c.setFont("P", 8.2)
        c.drawString(CARD_X + 42, y - 21, "%d positions" % len(ch["items"]))
        c.setFillColor(INK); c.setFont("PM", 10)
        c.drawRightString(W - CARD_X, y - 8, str(ctx["chapter_pages"][ci]))
        c.setStrokeColor(LINE); c.setDash(1, 2); c.line(CARD_X + 42, y - 28, W - CARD_X, y - 28); c.setDash()
        y -= 47
    extras = [("Tips for a Great Night", ctx["tips_page"]), ("Our Favorites checklist", ctx["fav_page"])]
    for t, p in extras:
        c.setFillColor(INK); c.setFont("PM", 10); c.drawString(CARD_X + 42, y - 4, t)
        c.drawRightString(W - CARD_X, y - 4, str(p)); y -= 24


def page_chapter(c, ctx):
    ci = ctx["ci"]; ch = CHAPTERS[ci]
    col = HexColor(CHAPTER_COLORS[ci])
    c.setFillColor(PLUM); c.rect(0, 0, W, H, stroke=0, fill=1)
    glow(c, W * 0.8, H * 0.78, 210, col, alpha=0.04)
    c.setFillColor(col); c.setFillAlpha(0.22)
    c.setFont("PB", 190); c.drawString(14, H - 270, "%02d" % (ci + 1))
    c.setFillAlpha(1)
    centered_y = H * 0.40
    c.setFillColor(HexColor("#ffffff"))
    y = centered_y + 40
    size = 30
    lines = simpleSplit(ch["title"], "PB", size, W - 2 * 40)
    c.setFont("PB", size)
    for ln in lines:
        c.drawString(40, y, ln); y -= size * 1.18
    if ch.get("spicy"):
        flame(c, 40 + pdfmetrics.stringWidth(lines[-1], "PB", size) + 24, y + size * 0.5, 30, PINK, GOLD)
    c.setFillColor(col); c.rect(40, y + 2, 54, 4, stroke=0, fill=1)
    y -= 24
    y = para(c, ch["blurb"], 40, y, W - 2 * 40 - 20, "PL", 11.2, 17.5, HexColor("#eadcf0"))
    c.setFillColor(HexColor("#bfa5cb")); c.setFont("PM", 9)
    c.drawString(40, 56, "%d POSITIONS" % len(ch["items"]))


def draw_card(c, top, num, item, col):
    name, vibe, how, tip, comfort, intimacy, energy = item
    x, w = CARD_X, CARD_W
    bottom = top - CARD_H
    c.setFillColor(HexColor("#ffffff")); c.setStrokeColor(LINE); c.setLineWidth(0.8)
    c.roundRect(x, bottom, w, CARD_H, 12, stroke=1, fill=1)
    c.setFillColor(col); c.circle(x + 28, top - 29, 15.5, stroke=0, fill=1)
    centered(c, str(num), x + 28, top - 33.2, "PB", 12 if num < 100 else 9.5, HexColor("#ffffff"))
    c.setFillColor(INK)
    nsize = min(17, 17 * (w - 66) / max(pdfmetrics.stringWidth(name, "PB", 17), 1))
    c.setFont("PB", nsize); c.drawString(x + 54, top - 26, name)
    c.setFillColor(col); c.setFont("PI", 9.2); c.drawString(x + 54, top - 40, vibe)
    c.setStrokeColor(LINE); c.line(x + 18, top - 54, x + w - 18, top - 54)
    y = top - 72
    y = para(c, how, x + 18, y, w - 36, "P", 10.3, 16, INK)
    y -= 6
    tip_lines = simpleSplit(tip, "PM", 9.3, w - 36 - 44)
    th = 16 + 13.6 * len(tip_lines)
    c.setFillColor(col); c.setFillAlpha(0.10); c.roundRect(x + 18, y - th, w - 36, th, 7, stroke=0, fill=1)
    c.setFillAlpha(1)
    c.setFillColor(col); c.rect(x + 18, y - th, 3.2, th, stroke=0, fill=1)
    c.setFont("PB", 7.8); c.drawString(x + 30, y - 16.6, "TIP")
    ty = y - 16.6
    c.setFillColor(INK); c.setFont("PM", 9.3)
    for ln in tip_lines:
        c.drawString(x + 56, ty, ln); ty -= 13.6
    tip_bottom = y - th
    ry = bottom + 20
    assert tip_bottom > ry + 12, "text too long for card: %s" % name
    c.setStrokeColor(LINE); c.line(x + 18, bottom + 36, x + w - 18, bottom + 36)
    gx = x + 18
    for label, val in (("Comfort", comfort), ("Intimacy", intimacy), ("Energy", energy)):
        c.setFillColor(MUTED); c.setFont("PM", 7.8); c.drawString(gx, ry - 2.4, label)
        dots(c, gx + 40, ry, val, col)
        gx += 112


def page_cards(c, ctx):
    ci = ctx["ci"]
    col = HexColor(CHAPTER_COLORS[ci])
    inner_bg(c, ctx, ctx["right"])
    top = H - 52
    for num, item in ctx["items"]:
        draw_card(c, top, num, item, col)
        top -= CARD_H + 22


def page_tips(c, ctx):
    inner_bg(c, ctx, "Tips for a great night")
    title_block(c, "Tips for a Great Night")
    y = H - 118
    for i, (h, t) in enumerate(TIPS):
        lines = simpleSplit(t, "P", 8.8, W - 2 * CARD_X - 40)
        hh = 28 + 12.5 * len(lines)
        c.setFillColor(HexColor("#ffffff")); c.setStrokeColor(LINE)
        c.roundRect(CARD_X, y - hh, W - 2 * CARD_X, hh, 9, stroke=1, fill=1)
        flame(c, CARD_X + 20, y - hh / 2 - 8, 17, PINK, GOLD)
        c.setFillColor(INK); c.setFont("PB", 10); c.drawString(CARD_X + 40, y - 19, h)
        para(c, t, CARD_X + 40, y - 33, W - 2 * CARD_X - 54, "P", 8.8, 12.5, INK)
        y -= hh + 9


def page_fav(c, ctx):
    inner_bg(c, ctx, "Our Favorites")
    title_block(c, "Our Favorites", "Tick the ones you love and want to try again.")
    items = ctx["fav"]
    per_col = 26 if len(items) > 20 else len(items)
    colw = (W - 2 * CARD_X) / 2
    for idx, (num, name, ci) in enumerate(items):
        col_i, row = divmod(idx, per_col)
        x = CARD_X + col_i * colw
        y = H - 142 - row * 15.4
        c.setStrokeColor(HexColor(CHAPTER_COLORS[ci])); c.setLineWidth(0.9)
        c.rect(x, y - 1, 8, 8, stroke=1, fill=0)
        c.setFillColor(MUTED); c.setFont("PM", 6.6); c.drawString(x + 13, y + 0.6, "%d" % num)
        c.setFillColor(INK); c.setFont("P", 7.9)
        label = name
        while pdfmetrics.stringWidth(label, "P", 7.9) > colw - 42:
            label = label[:-1]
        c.drawString(x + 27, y, label)


def page_upsell(c, ctx):
    inner_bg(c, ctx, "Want more?")
    title_block(c, "Want More?")
    cx = W / 2
    c.setFillColor(PLUM); c.roundRect(CARD_X, 150, W - 2 * CARD_X, 290, 16, stroke=0, fill=1)
    glow(c, cx, 330, 150, PINK, alpha=0.03)
    flame(c, cx, 345, 70, PINK, GOLD)
    centered(c, "PREMIUM PLAN", cx, 316, "PB", 21, HexColor("#ffffff"))
    centered(c, "100 exclusive & unique positions", cx, 292, "PM", 11, GOLD)
    for i, t in enumerate(["Eight themed chapters", "Face to face, rider, side by side, from behind",
                           "Seated, standing and furniture positions", "More spicy positions"]):
        centered(c, t, cx, 262 - i * 20, "P", 9.8, HexColor("#e9d9ee"))
    flame(c, cx + 62, 190, 16, PINK, GOLD)
    centered(c, "Available on the website as the Premium Plan", cx, 168, "PI", 9, HexColor("#cdb6d6"))


def page_end(c, ctx):
    c.setFillColor(PLUM); c.rect(0, 0, W, H, stroke=0, fill=1)
    glow(c, W / 2, H * 0.55, 220, PINK, alpha=0.03)
    flame(c, W / 2, H - 230, 62, PINK, GOLD)
    centered(c, "Thank you", W / 2, H - 290, "PB", 30, HexColor("#ffffff"))
    centered(c, "Be kind, be curious, and enjoy each other.", W / 2, H - 316, "PI", 11, HexColor("#e9d9ee"))
    y = 150
    for t in ["This guide is for personal use by the purchaser only.",
              "Please do not copy, share or resell it.",
              "For adults aged 18 and over. General education only, not medical advice.",
              "(c) %s %s. All rights reserved." % (YEAR, BRAND.title())]:
        centered(c, t, W / 2, y, "PL", 8, HexColor("#b9a1c6")); y -= 13


PAGES = {"cover": page_cover, "welcome": page_welcome, "rules": page_rules, "howto": page_howto,
         "toc": page_toc, "chapter": page_chapter, "cards": page_cards, "tips": page_tips,
         "fav": page_fav, "upsell": page_upsell, "end": page_end}
NO_FOOTER = {"cover", "chapter", "end"}

MOODS_PREMIUM = [("Want closeness?", "Try Face to Face, Side by Side or the Heart Lock."),
                 ("Want to stay relaxed?", "Side by Side positions and the Pillow Lift take the effort out."),
                 ("Want to share control?", "The Rider chapter lets whoever is on top set the pace."),
                 ("Feeling adventurous?", "Standing, furniture and the spicy chapter add variety."),
                 ("Short on energy?", "Look for one or two dots under Energy.")]
MOODS_BASIC = [("Want closeness?", "Try Classic Missionary, Classic Spooning or the Mirror Side."),
               ("Want to stay relaxed?", "Spooning and the Pillow Lift keep effort low."),
               ("Want to share control?", "The Rider and Reverse Rider let the partner on top lead."),
               ("Feeling adventurous?", "Try Standing Embrace or the Edge of the Bed.")]


def build(path, plan):
    allitems = []
    for ci, ch in enumerate(CHAPTERS):
        for it in ch["items"]:
            allitems.append((ci, it))
    plan_pages = [{"t": "cover"}, {"t": "welcome"}, {"t": "rules"}, {"t": "howto"}]
    chapter_pages = {}
    if plan == "premium":
        plan_pages.append({"t": "toc"})
        num = 0
        for ci, ch in enumerate(CHAPTERS):
            chapter_pages[ci] = len(plan_pages) + 1
            plan_pages.append({"t": "chapter", "ci": ci})
            numbered = [(num + i + 1, it) for i, it in enumerate(ch["items"])]
            num += len(numbered)
            for k in range(0, len(numbered), 2):
                plan_pages.append({"t": "cards", "ci": ci, "items": numbered[k:k + 2], "right": ch["title"]})
        fav = [(i + 1, it[0], ci) for i, (ci, it) in enumerate(allitems)]
        tips_page = len(plan_pages) + 1
        plan_pages.append({"t": "tips"})
        fav_page = len(plan_pages) + 1
        plan_pages += [{"t": "fav", "fav": fav[:50]}, {"t": "fav", "fav": fav[50:]}, {"t": "end"}]
        meta = dict(plan="Premium Plan", sub="100 Exclusive Positions", moods=MOODS_PREMIUM)
        title = BRAND.title() + " - Premium Plan (100 positions)"
    else:
        lookup = {it[0]: (ci, it) for ci, it in allitems}
        chosen = [lookup[n] for n in BASIC_NAMES]
        numbered = [(i + 1, it) for i, (ci, it) in enumerate(chosen)]
        for k in range(0, len(numbered), 2):
            plan_pages.append({"t": "cards", "ci": 0, "items": numbered[k:k + 2], "right": "Your starter ten"})
        tips_page = len(plan_pages) + 1
        plan_pages.append({"t": "tips"})
        fav_page = len(plan_pages) + 1
        plan_pages += [{"t": "fav", "fav": [(i + 1, it[0], 0) for i, (ci, it) in enumerate(chosen)]},
                       {"t": "upsell"}, {"t": "end"}]
        meta = dict(plan="Basic Plan", sub="10 Good & Unique Positions", moods=MOODS_BASIC)
        title = BRAND.title() + " - Basic Plan (10 positions)"

    c = canvas.Canvas(path, pagesize=A5)
    c.setTitle(title); c.setAuthor(BRAND.title()); c.setSubject("Adult relationship guide (18+)")
    c.setPageCompression(1)
    for i, pg in enumerate(plan_pages, 1):
        ctx = dict(meta, pageno=i, tips_page=tips_page, fav_page=fav_page,
                   chapter_pages=[chapter_pages.get(k) for k in range(len(CHAPTERS))])
        ctx.update({k: v for k, v in pg.items() if k != "t"})
        PAGES[pg["t"]](c, ctx)
        c.showPage()
    c.save()
    return len(plan_pages)


if __name__ == "__main__":
    out = os.path.join(HERE, "..", "private")
    os.makedirs(out, exist_ok=True)
    nb = build(os.path.join(out, "basic-guide.pdf"), "basic")
    npg = build(os.path.join(out, "premium-guide.pdf"), "premium")
    print("basic pages:", nb, "premium pages:", npg)
