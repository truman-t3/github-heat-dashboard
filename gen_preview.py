from PIL import Image, ImageDraw, ImageFont
import os

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

img = Image.new("RGB", (W, H), bg)
d = ImageDraw.Draw(img)

# eyebrow
d.text((64, 70), "GITHUB  ·  ACTIVITY", font=font(20), fill=accent)
# title
d.text((60, 116), "GitHub 项目热度看板", font=font(60), fill=text)
# subtitle
d.text((62, 212), "零依赖 · 本地优先 · 含 Star / Fork / 克隆 / 浏览 / 流量来源 + 长期趋势",
       font=font(26), fill=muted)

# decorative accent tick under title
d.rectangle([64, 286, 67, 304], fill=accent)

# mini bar chart (clone ranking示意)
bars = [0.96, 0.62, 0.40, 0.28, 0.18]
bx, by, bw, bgap, bh_max = 64, 360, 92, 42, 160
for i, v in enumerate(bars):
    x = bx + i * (bw + bgap)
    h = int(bh_max * v)
    col = accent if i == 0 else bar
    d.rectangle([x, by + bh_max - h, x + bw, by + bh_max], fill=col)

# footer line
d.text((64, 560), "github-heat-dashboard  ·  MIT License", font=font(20), fill=muted)

img.save("preview.png")
print("preview.png saved:", os.path.getsize("preview.png"), "bytes")
