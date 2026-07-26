from PIL import Image, ImageDraw, ImageFont
import os, json, re

W, H = 1200, 630
bg     = (14, 14, 16)
text   = (233, 230, 223)
muted  = (142, 139, 132)
accent = (194, 168, 120)
bar    = (58, 58, 60)

font_path = "C:/Windows/Fonts/msyh.ttc"
def font(sz):
    try:
        return ImageFont.truetype(font_path, sz)
    except Exception:
        return ImageFont.load_default()

# --- 读取真实数据（data.js 是 JSON 而非 Python，用 raw_decode 精确提取） ---
src = open("data.js", "r", encoding="utf-8").read()
_dec = json.JSONDecoder()
def grab(name):
    i = src.index("window." + name + " = ") + len("window." + name + " = ")
    obj, _ = _dec.raw_decode(src, i)
    return obj

D = grab("DASHBOARD_DATA")
Hhist = grab("DASHBOARD_HISTORY")
S = grab("STAR_HISTORY")

repos = [r for r in D["repos"] if not r.get("private")]
repos.sort(key=lambda r: -(r.get("clones") or 0))
totalStars = sum((r.get("stars") or 0) for r in D["repos"])
totalClones = sum((r.get("clones") or 0) for r in D["repos"])
histDays = len(Hhist)
starPts = len(S.get("total", []))

img = Image.new("RGB", (W, H), bg)
d = ImageDraw.Draw(img)

# eyebrow + title
d.text((64, 70), "GITHUB  ·  ACTIVITY", font=font(20), fill=accent)
d.text((60, 116), "GitHub 项目热度看板", font=font(60), fill=text)
d.text((62, 212), "零依赖 · 本地优先 · 含 Star / Fork / 克隆 / 浏览 / 流量来源 + 趋势",
       font=font(26), fill=muted)
d.rectangle([64, 286, 67, 304], fill=accent)

# 真实克隆排行（Top 5 公开仓库）
top = repos[:5]
bx, by, bw, bgap, bh_max = 64, 330, 150, 30, 150
maxc = max(1, *[r.get("clones") or 0 for r in top])
for i, r in enumerate(top):
    v = r.get("clones") or 0
    h = int(bh_max * (v / maxc))
    x = bx + i * (bw + bgap)
    col = accent if i == 0 else bar
    d.rectangle([x, by + bh_max - h, x + bw, by + bh_max], fill=col)
    nm = r["name"]
    if len(nm) > 12:
        nm = nm[:11] + "…"
    d.text((x + bw // 2, by + bh_max + 18), str(v), font=font(16), fill=muted, anchor="mm")
    d.text((x + bw // 2, by + bh_max + 42), nm, font=font(18), fill=text, anchor="mm")

# footer summary（真实指标）
summary = f"\u2605 {totalStars}   \u2b07 {totalClones} \u514b\u9686/14d   \u00b7  {histDays} \u5929\u8d8b\u52bf   \u00b7  {starPts} \u4e2a Star \u5386\u53f2\u70b9"
d.text((64, 560), summary, font=font(22), fill=muted)

img.save("preview.png")
print("preview.png saved:", os.path.getsize("preview.png"), "bytes | stars:", totalStars,
      "clones:", totalClones, "histDays:", histDays, "starPts:", starPts)
