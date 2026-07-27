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
totalForks = sum((r.get("forks") or 0) for r in D["repos"])
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

# footer summary（仅公开指标 Star / Fork，不暴露 owner-only 流量）
summary = f"\u2605 {totalStars} Stars    \ud83c\udf74 {totalForks} Forks    \u00b7  \u96f6\u4f9d\u8d56\u672c\u5730\u770b\u677f"
d.text((64, 560), summary, font=font(22), fill=muted)

img.save("preview.png")
print("preview.png saved:", os.path.getsize("preview.png"), "bytes | stars:", totalStars,
      "clones:", totalClones, "histDays:", histDays, "starPts:", starPts)
