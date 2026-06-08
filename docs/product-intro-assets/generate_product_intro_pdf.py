from __future__ import annotations

import math
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / "docs" / "product-intro-assets"
OUT_PDF = ROOT / "docs" / "爪爪电商短视频工作流_产品介绍_精修版.pdf"

W, H = 1600, 900

COLORS = {
    "bg": "#F7FAF2",
    "bg2": "#EEF8E7",
    "ink": "#172018",
    "muted": "#667064",
    "line": "#DDE8D3",
    "accent": "#82E600",
    "accent2": "#B9FF67",
    "dark": "#0C120E",
    "white": "#FFFFFF",
    "card": "#FFFFFF",
    "soft": "#F1F5EC",
}


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    font_dir = ROOT / "resource" / "fonts"
    candidates = {
        "bold": [
            font_dir / "MicrosoftYaHeiBold.ttc",
            font_dir / "STHeitiMedium.ttc",
        ],
        "regular": [
            font_dir / "MicrosoftYaHeiNormal.ttc",
            font_dir / "STHeitiLight.ttc",
        ],
    }[name]
    for p in candidates:
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


F = {
    "h1": font("bold", 68),
    "h2": font("bold", 44),
    "h3": font("bold", 30),
    "h4": font("bold", 24),
    "body": font("regular", 24),
    "body_b": font("bold", 24),
    "small": font("regular", 18),
    "small_b": font("bold", 18),
    "tiny": font("regular", 15),
    "num": font("bold", 52),
}


def new_page(bg: str = COLORS["bg"]) -> Image.Image:
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 5), fill=COLORS["accent"])
    return img


def draw_logo(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 72) -> None:
    draw.rounded_rectangle((x, y, x + size, y + size), radius=16, fill=COLORS["dark"])
    mark_font = font("bold", int(size * 0.44))
    text = "爪"
    bbox = draw.textbbox((0, 0), text, font=mark_font)
    tx = x + (size - (bbox[2] - bbox[0])) / 2
    ty = y + (size - (bbox[3] - bbox[1])) / 2 - size * 0.05
    draw.text((tx, ty), text, font=mark_font, fill=COLORS["accent"])


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=fnt)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_text(text: str, max_width: int, fnt: ImageFont.FreeTypeFont, draw: ImageDraw.ImageDraw) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        para = para.strip()
        if not para:
            lines.append("")
            continue
        current = ""
        for ch in para:
            candidate = current + ch
            if text_size(draw, candidate, fnt)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = ch
        if current:
            lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    max_width: int,
    fnt: ImageFont.FreeTypeFont,
    fill: str = COLORS["ink"],
    line_gap: int = 10,
    max_lines: int | None = None,
) -> int:
    x, y = xy
    lines = wrap_text(text, max_width, fnt, draw)
    if max_lines is not None:
        lines = lines[:max_lines]
    line_h = text_size(draw, "国", fnt)[1] + line_gap
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += line_h
    return y


def badge(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fill: str = COLORS["bg2"]) -> None:
    x, y = xy
    tw, th = text_size(draw, text, F["small_b"])
    draw.rounded_rectangle((x, y, x + tw + 26, y + th + 16), radius=16, fill=fill, outline=COLORS["line"])
    draw.text((x + 13, y + 8), text, font=F["small_b"], fill=COLORS["ink"])


def card(draw: ImageDraw.ImageDraw, xyxy: tuple[int, int, int, int], radius: int = 24, fill: str = COLORS["card"]) -> None:
    draw.rounded_rectangle(xyxy, radius=radius, fill=fill, outline=COLORS["line"], width=2)


def add_header(draw: ImageDraw.ImageDraw, page_title: str, page_no: int) -> None:
    draw_logo(draw, 70, 42, 46)
    draw.text((130, 49), "爪爪电商短视频工作流", font=F["small_b"], fill=COLORS["ink"])
    draw.text((70, 825), f"{page_no:02d}", font=F["small_b"], fill=COLORS["muted"])
    draw.text((116, 825), page_title, font=F["small"], fill=COLORS["muted"])


def add_image_cover(
    page: Image.Image,
    path: Path,
    box: tuple[int, int, int, int],
    radius: int = 28,
    crop: bool = True,
) -> None:
    if not path.exists():
        return
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    im = Image.open(path).convert("RGB")
    if crop:
        im = ImageOps.fit(im, (bw, bh), method=Image.Resampling.LANCZOS, centering=(0.5, 0.35))
    else:
        im.thumbnail((bw, bh), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (bw, bh), COLORS["soft"])
        canvas.paste(im, ((bw - im.width) // 2, (bh - im.height) // 2))
        im = canvas
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw, bh), radius=radius, fill=255)
    page.paste(im, (x1, y1), mask)
    draw = ImageDraw.Draw(page)
    draw.rounded_rectangle(box, radius=radius, outline=COLORS["line"], width=2)


def add_image_contain(
    page: Image.Image,
    path: Path,
    box: tuple[int, int, int, int],
    radius: int = 24,
    bg: str = COLORS["white"],
) -> None:
    if not path.exists():
        return
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    im = Image.open(path).convert("RGB")
    im.thumbnail((bw, bh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (bw, bh), bg)
    canvas.paste(im, ((bw - im.width) // 2, (bh - im.height) // 2))
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw, bh), radius=radius, fill=255)
    page.paste(canvas, (x1, y1), mask)
    ImageDraw.Draw(page).rounded_rectangle(box, radius=radius, outline=COLORS["line"], width=2)


def draw_section_label(draw: ImageDraw.ImageDraw, x: int, y: int, label: str) -> None:
    draw.text((x, y), label.upper(), font=F["tiny"], fill=COLORS["muted"])
    draw.line((x, y + 28, x + 120, y + 28), fill=COLORS["accent"], width=4)


def dark_pill(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str) -> None:
    x, y = xy
    tw, th = text_size(draw, text, F["small_b"])
    draw.rounded_rectangle(
        (x, y, x + tw + 28, y + th + 18),
        radius=18,
        fill="#152018",
        outline="#37552A",
        width=2,
    )
    draw.text((x + 14, y + 9), text, font=F["small_b"], fill="#DDFBCC")


def phone_frame(page: Image.Image, path: Path, box: tuple[int, int, int, int]) -> None:
    draw = ImageDraw.Draw(page)
    x1, y1, x2, y2 = box
    draw.rounded_rectangle((x1, y1, x2, y2), radius=48, fill=COLORS["dark"])
    inner = (x1 + 18, y1 + 18, x2 - 18, y2 - 18)
    add_image_cover(page, path, inner, radius=34, crop=True)
    draw.rounded_rectangle((x1 + 116, y1 + 18, x2 - 116, y1 + 36), radius=9, fill=COLORS["dark"])


def page_cover_refined() -> Image.Image:
    page = new_page(COLORS["dark"])
    draw = ImageDraw.Draw(page)
    draw.rectangle((0, 0, 640, H), fill=COLORS["dark"])
    draw.rectangle((640, 0, W, H), fill=COLORS["bg"])
    draw.ellipse((1080, -240, 1780, 430), fill="#E8FFD0")
    draw.ellipse((1220, 520, 1880, 1160), fill="#F1F8EA")
    draw_logo(draw, 76, 76, 86)
    draw.text((190, 84), "爪爪电商短视频工作流", font=F["h3"], fill=COLORS["white"])
    draw.text((190, 128), "AI commerce video workflow", font=F["small"], fill="#A8B3A6")
    draw.text((76, 230), "把爆款视频的", font=F["h1"], fill=COLORS["white"])
    draw.text((76, 310), "成功经验", font=F["h1"], fill=COLORS["accent"])
    draw.text((76, 390), "变成可复用流程", font=F["h1"], fill=COLORS["white"])
    draw_wrapped(
        draw,
        "面向电商、本地生活和门店老板：参考成功视频，自动生成文案、素材组合、配音、字幕和短视频成片。",
        (80, 505),
        470,
        F["body"],
        "#D6DED2",
        line_gap=12,
    )
    dark_pill(draw, (78, 664), "爆款链接拆解")
    dark_pill(draw, (260, 664), "AI 改编文案")
    dark_pill(draw, (78, 728), "真实素材优先")
    dark_pill(draw, (260, 728), "中文用户友好")

    phone_frame(page, ASSET_DIR / "mobile.png", (1010, 82, 1368, 824))
    card(draw, (745, 620, 1048, 780), radius=24, fill=COLORS["white"])
    draw.text((778, 652), "定位", font=F["h4"], fill=COLORS["ink"])
    draw_wrapped(draw, "不是单点视频生成器，而是一套可持续测试、复刻和生产短视频的工作流。", (778, 694), 230, F["small"], COLORS["muted"])
    draw.text((76, 820), "产品介绍精修版 · 2026-06-05", font=F["small"], fill="#A8B3A6")
    return page


def page_readme_foundation(page_no: int) -> Image.Image:
    page = new_page()
    draw = ImageDraw.Draw(page)
    add_header(draw, "官方底座能力", page_no)
    draw_section_label(draw, 76, 112, "selected from readme")
    draw.text((76, 156), "MoneyPrinterTurbo 提供稳定的视频生成底座。", font=F["h2"], fill=COLORS["ink"])
    draw_wrapped(
        draw,
        "原项目 README 的核心表述是：用户只需提供视频主题或关键词，系统即可自动生成视频文案、视频素材、字幕、背景音乐，并合成高清短视频。爪爪在这个底座上增加电商爆款拆解和中文傻瓜化流程。",
        (80, 220),
        700,
        F["body"],
        COLORS["muted"],
        line_gap=12,
    )
    features = [
        "Web 界面 + API",
        "AI 自动文案 / 自定义文案",
        "9:16 与 16:9 高清尺寸",
        "批量视频生成",
        "多语音合成与试听",
        "字幕样式可调",
        "背景音乐与音量控制",
        "高清素材库 + 本地素材",
        "多模型供应商接入",
    ]
    x, y = 82, 385
    for i, item in enumerate(features):
        bx = x + (i % 3) * 235
        by = y + (i // 3) * 72
        badge(draw, (bx, by), item, COLORS["white"])
    add_image_contain(page, ROOT / "docs/webui.jpg", (885, 106, 1510, 802), radius=28, bg="#FAFBF8")
    draw.text((900, 816), "README 官方 WebUI 截图：用于说明底座能力，不作为当前爪爪 UI 的最终样式。", font=F["tiny"], fill=COLORS["muted"])
    return page


def page_zaozhao_layer(page_no: int) -> Image.Image:
    page = new_page()
    draw = ImageDraw.Draw(page)
    add_header(draw, "爪爪增强层", page_no)
    draw.text((74, 122), "我们不重写底座，而是把它变成电商可用的产品。", font=F["h2"], fill=COLORS["ink"])
    draw_wrapped(
        draw,
        "用户不需要理解 LLM、TTS、Pexels、字幕或合成参数；运营侧先配置好 API 和默认选项，用户只需要围绕“爆款参考 + 商品卖点 + 真实素材”完成少量输入。",
        (78, 188),
        1260,
        F["body"],
        COLORS["muted"],
        line_gap=12,
    )
    left = [
        ("输入收敛", "商品/店铺名称、卖点、可选爆款链接、可选真实素材"),
        ("AI 改编", "提取参考视频的节奏、镜头语言、钩子结构，再改写成自有商品文案"),
        ("素材策略", "真实图片/视频优先；不足时用平台素材库补足镜头"),
    ]
    right = [
        ("配音傻瓜化", "默认智能音色库，用户只选音色；成品录音可直接上传"),
        ("中文体验", "必填/可选清晰标注，减少英文和后台参数暴露"),
        ("可扩展", "后续接数字人、方言音色、自动发布和数据反馈"),
    ]
    for col, group in enumerate([left, right]):
        x = 90 + col * 720
        for row, (title, body) in enumerate(group):
            y = 320 + row * 150
            card(draw, (x, y, x + 610, y + 118), radius=22)
            draw.text((x + 28, y + 24), title, font=F["h4"], fill=COLORS["ink"])
            draw_wrapped(draw, body, (x + 160, y + 24), 395, F["small"], COLORS["muted"], line_gap=8)
    card(draw, (90, 778, 1425, 835), radius=18, fill=COLORS["dark"])
    draw.text((122, 795), "一句话：官方底座负责“能生成”，爪爪增强层负责“让电商用户真的会用、愿意用、反复用”。", font=F["body_b"], fill=COLORS["white"])
    return page


def page_process_refined(page_no: int) -> Image.Image:
    page = new_page()
    draw = ImageDraw.Draw(page)
    add_header(draw, "产品流程", page_no)
    draw.text((74, 120), "从参考内容到发布素材，形成闭环。", font=F["h2"], fill=COLORS["ink"])
    steps = [
        ("爆款输入", "粘贴抖音/TikTok 等公开视频链接，或直接输入商品信息"),
        ("风格提取", "解析标题、简介、标签，AI 总结节奏、开场钩子、镜头语言"),
        ("文案改编", "生成电商口播脚本、关键词和发布标题，不复制原视频内容"),
        ("素材组合", "优先使用门店/商品真实素材，缺镜头再自动检索平台素材"),
        ("声音字幕", "选择平台音色或上传成品录音，自动生成字幕和背景音乐"),
        ("成片交付", "输出 9:16 竖屏短视频，可下载、复用或批量测试"),
    ]
    y = 220
    for i, (title, body) in enumerate(steps, 1):
        x = 120 + (i - 1) * 230
        draw.ellipse((x, y, x + 92, y + 92), fill=COLORS["dark"])
        draw.text((x + 32, y + 26), f"{i}", font=F["h3"], fill=COLORS["accent"])
        if i < len(steps):
            draw.line((x + 100, y + 46, x + 218, y + 46), fill=COLORS["accent"], width=5)
        card(draw, (x - 45, y + 135, x + 170, y + 365), radius=22)
        draw.text((x - 18, y + 166), title, font=F["h4"], fill=COLORS["ink"])
        draw_wrapped(draw, body, (x - 18, y + 212), 160, F["tiny"], COLORS["muted"], line_gap=7)
    card(draw, (120, 700, 1480, 800), radius=24, fill=COLORS["white"])
    draw.text((154, 728), "对用户来说，只是一个很短的表单；对系统来说，是完整的视频生产流水线。", font=F["h3"], fill=COLORS["ink"])
    return page


def page_visual_assets(page_no: int) -> Image.Image:
    page = new_page()
    draw = ImageDraw.Draw(page)
    add_header(draw, "真实素材策略", page_no)
    draw.text((74, 120), "AI 可以补镜头，但真实商品/门店素材决定可信度。", font=F["h2"], fill=COLORS["ink"])
    draw_wrapped(
        draw,
        "餐饮、本地生活和电商展示最怕“看起来像假图”。因此产品把本地素材作为第一优先级：老板照片、门店环境、菜品细节、商品包装都可以成为真实感来源。",
        (78, 184),
        840,
        F["body"],
        COLORS["muted"],
        line_gap=12,
    )
    add_image_cover(page, ROOT / "storage/local_videos/1cae78e9-be7c-472e-b587-378eecb40f8a_b75345c8179110f82f1e2a1917134375.jpg", (970, 92, 1510, 455), radius=26)
    add_image_cover(page, ROOT / "storage/local_videos/62980d30-1345-429a-9e48-0897c5cd2171_a659b3adbd57f63dbe300f72c53cc8bd.jpg", (970, 492, 1225, 805), radius=22)
    add_image_cover(page, ROOT / "storage/local_videos/1f0190f6-54ea-4305-a7b7-86b87e049280_1dbbf9de1f396763ff0a381a90b1b424.jpg", (1255, 492, 1510, 805), radius=22)
    rows = [
        ("真实素材优先", "用户上传的菜品、商品、门店、人物素材优先参与合成。"),
        ("素材库补充", "Pexels/Pixabay 负责补足空镜、环境和转场素材。"),
        ("可控输出", "用户可以控制是否用本地素材、片段时长、拼接模式和字幕样式。"),
    ]
    y = 360
    for title, body in rows:
        card(draw, (82, y, 845, y + 118), radius=22)
        draw.text((112, y + 24), title, font=F["h4"], fill=COLORS["ink"])
        draw_wrapped(draw, body, (300, y + 28), 485, F["small"], COLORS["muted"], line_gap=8)
        y += 145
    return page


def page_api_readme(page_no: int) -> Image.Image:
    page = new_page()
    draw = ImageDraw.Draw(page)
    add_header(draw, "Web + API 双入口", page_no)
    draw.text((74, 120), "README 的 API 能力适合后续产品化集成。", font=F["h2"], fill=COLORS["ink"])
    draw_wrapped(
        draw,
        "官方底座提供视频生成、字幕生成、音频生成、任务查询、音乐/素材上传、脚本和关键词生成等接口。当前 WebUI 面向普通用户，API 则为后续小程序、桌面端、自动发布和批量任务预留空间。",
        (78, 184),
        650,
        F["body"],
        COLORS["muted"],
        line_gap=12,
    )
    endpoints = ["/api/v1/videos", "/api/v1/subtitle", "/api/v1/audio", "/api/v1/tasks/{id}", "/api/v1/musics", "/api/v1/scripts", "/api/v1/terms"]
    y = 420
    for ep in endpoints:
        draw.rounded_rectangle((90, y, 520, y + 46), radius=13, fill=COLORS["white"], outline=COLORS["line"])
        draw.text((112, y + 12), ep, font=F["small_b"], fill=COLORS["ink"])
        y += 56
    add_image_contain(page, ROOT / "docs/api.jpg", (780, 110, 1515, 790), radius=26, bg="#FFFFFF")
    return page


def page_deployment_readme(page_no: int) -> Image.Image:
    page = new_page()
    draw = ImageDraw.Draw(page)
    add_header(draw, "部署与配置", page_no)
    draw.text((74, 120), "从本地试用到团队部署，路径清晰。", font=F["h2"], fill=COLORS["ink"])
    blocks = [
        ("推荐系统", "Windows 10+、macOS 11+、主流 Linux"),
        ("最低配置", "4 核 CPU / 4GB RAM；依赖云端 LLM、TTS 时 GPU 非必须"),
        ("推荐配置", "6-8 核 CPU / 8GB RAM；批量生成建议更高配置"),
        ("部署方式", "Windows 一键包、本地 uv、Docker、Google Colab"),
        ("关键配置", "LLM Provider、Pexels/Pixabay、TTS、字幕和素材路径"),
        ("运营策略", "API Key 统一配置，普通用户无需自行填写"),
    ]
    for i, (title, body) in enumerate(blocks):
        x = 84 + (i % 3) * 486
        y = 250 + (i // 3) * 210
        card(draw, (x, y, x + 420, y + 155), radius=24)
        draw.text((x + 28, y + 28), title, font=F["h4"], fill=COLORS["ink"])
        draw_wrapped(draw, body, (x + 28, y + 76), 340, F["small"], COLORS["muted"], line_gap=8)
    card(draw, (84, 725, 1510, 805), radius=22, fill=COLORS["dark"])
    draw.text((116, 750), "产品建议：对外用户只开放“傻瓜化生成页”，后台配置和 API Key 管理由运营侧统一维护。", font=F["body_b"], fill=COLORS["white"])
    return page


def page_validation_refined(page_no: int) -> Image.Image:
    page = new_page()
    draw = ImageDraw.Draw(page)
    add_header(draw, "当前测试结论", page_no)
    draw.text((74, 120), "核心链路已经可以进入真实 API 试用阶段。", font=F["h2"], fill=COLORS["ink"])
    add_metric(draw, 110, 250, "96", "pytest 通过")
    add_metric(draw, 370, 250, "0", "编译错误")
    add_metric(draw, 610, 250, "29+", "MiniMax 音色选项")
    add_metric(draw, 910, 250, "9:16", "默认输出比例")
    checks = [
        "LLM 文案 / 关键词 / 爆款风格 / 发布标题生成通过",
        "MiniMax TTS 抽测通过，旧音色配置具备兜底",
        "Pexels 素材搜索与下载通过",
        "本地素材 + TTS 成片通过",
        "本地素材 + 自定义音频成片通过",
        "上传接口、下载接口、路径安全拦截通过",
        "WebUI 首页和后台入口检查通过",
    ]
    y = 430
    for item in checks:
        draw.ellipse((110, y + 8, 132, y + 30), fill=COLORS["accent"])
        draw.text((150, y), item, font=F["body"], fill=COLORS["ink"])
        y += 54
    card(draw, (88, 800, 1510, 846), radius=18, fill="#FFF8E7")
    draw.text((116, 812), "边界说明：真实抖音链接仍可能受平台风控；数字人口播和更强方言克隆属于下一阶段增强能力。", font=F["small_b"], fill=COLORS["ink"])
    return page


def add_metric(draw: ImageDraw.ImageDraw, x: int, y: int, value: str, label: str) -> None:
    draw.text((x, y), value, font=F["num"], fill=COLORS["ink"])
    draw.text((x, y + 66), label, font=F["small"], fill=COLORS["muted"])


def page_cover() -> Image.Image:
    page = new_page()
    draw = ImageDraw.Draw(page)
    draw.ellipse((1030, -160, 1780, 560), fill="#ECFFD6")
    draw.ellipse((1120, 440, 1740, 1080), fill="#F2F8ED")
    draw_logo(draw, 88, 76, 82)
    draw.text((190, 82), "爪爪电商短视频工作流", font=F["h2"], fill=COLORS["ink"])
    draw.text((192, 138), "面向电商、本地生活与门店老板的 AI 短视频生产系统", font=F["body"], fill=COLORS["muted"])

    draw.text((88, 240), "从爆款链接到成片，", font=F["h1"], fill=COLORS["ink"])
    draw.text((88, 318), "把短视频生产变成工作流。", font=F["h1"], fill=COLORS["ink"])
    draw_wrapped(
        draw,
        "系统先拆解成功视频的文案与风格，再结合商品卖点、真实素材、智能配音和字幕自动生成适合发布的电商宣传短视频。",
        (92, 420),
        720,
        F["body"],
        COLORS["muted"],
        line_gap=12,
    )
    badge(draw, (92, 550), "爆款风格拆解")
    badge(draw, (290, 550), "AI 文案改编")
    badge(draw, (470, 550), "真实素材混合")
    badge(draw, (660, 550), "智能音色库")

    add_image_cover(page, ASSET_DIR / "mobile.png", (1060, 84, 1388, 826), radius=34, crop=True)
    card(draw, (862, 650, 1162, 790), radius=22, fill=COLORS["dark"])
    draw.text((892, 682), "当前测试状态", font=F["h4"], fill=COLORS["white"])
    draw.text((892, 724), "核心链路已跑通", font=F["body_b"], fill=COLORS["accent2"])

    draw.text((92, 800), "产品介绍 PDF · 2026-06-05", font=F["small"], fill=COLORS["muted"])
    return page


def page_positioning(page_no: int) -> Image.Image:
    page = new_page()
    draw = ImageDraw.Draw(page)
    add_header(draw, "产品定位", page_no)
    draw.text((70, 125), "它解决的不是“做一个视频”，而是“持续复刻有效视频”。", font=F["h2"], fill=COLORS["ink"])
    draw_wrapped(
        draw,
        "传统工具从空白文案开始，用户要懂脚本、剪辑、配音和素材。爪爪的核心入口改成“参考成功视频”，让用户先给一个爆款链接，再由 AI 提取可迁移的节奏、镜头、卖点表达和口播结构。",
        (74, 195),
        1340,
        F["body"],
        COLORS["muted"],
        line_gap=13,
    )

    items = [
        ("目标用户", "餐饮门店、探店达人、电商卖家、本地生活商家、短视频代运营团队"),
        ("核心场景", "新品上架、门店引流、套餐推广、老板/主播口播、批量生成不同风格素材"),
        ("产品价值", "降低短视频制作门槛，减少从零写文案和找素材的时间，让成功内容经验可复用"),
    ]
    x = 74
    for title, body in items:
        card(draw, (x, 380, x + 452, 650), radius=24)
        draw.text((x + 34, 414), title, font=F["h3"], fill=COLORS["ink"])
        draw_wrapped(draw, body, (x + 34, 472), 370, F["body"], COLORS["muted"], line_gap=12)
        x += 496

    add_metric(draw, 130, 710, "96", "自动化测试通过")
    add_metric(draw, 390, 710, "3", "跳过测试")
    add_metric(draw, 650, 710, "9:16", "默认电商短视频比例")
    add_metric(draw, 930, 710, "29+", "当前可选智能音色")
    return page


def page_workflow(page_no: int) -> Image.Image:
    page = new_page()
    draw = ImageDraw.Draw(page)
    add_header(draw, "端到端流程", page_no)
    draw.text((70, 120), "用户侧流程：少填内容，多让系统自动判断。", font=F["h2"], fill=COLORS["ink"])

    steps = [
        ("01", "粘贴爆款链接", "抖音/TikTok 链接优先，解析标题、简介、标签和可迁移风格。"),
        ("02", "填写商品卖点", "商品/门店名、出镜身份、卖点场景，补齐个性化信息。"),
        ("03", "AI 改编文案", "生成口播文案、关键词、镜头节奏和字幕表达。"),
        ("04", "匹配素材", "优先使用真实上传素材，不足部分从平台素材库补充。"),
        ("05", "选择音色字幕", "默认平台音色即可生成；支持自定义音频跳过 TTS。"),
        ("06", "生成并下载", "输出竖屏短视频，带字幕、配音、背景音乐和封面预览。"),
    ]
    x_positions = [80, 560, 1040]
    y_positions = [250, 520]
    for i, (num, title, body) in enumerate(steps):
        x = x_positions[i % 3]
        y = y_positions[i // 3]
        card(draw, (x, y, x + 400, y + 200), radius=26)
        draw.text((x + 28, y + 26), num, font=F["h3"], fill=COLORS["accent"])
        draw.text((x + 92, y + 26), title, font=F["h3"], fill=COLORS["ink"])
        draw_wrapped(draw, body, (x + 30, y + 86), 330, F["small"], COLORS["muted"], line_gap=9)
        if i in (0, 1, 3, 4):
            draw.line((x + 410, y + 100, x + 464, y + 100), fill=COLORS["accent"], width=5)
    return page


def page_modules(page_no: int) -> Image.Image:
    page = new_page()
    draw = ImageDraw.Draw(page)
    add_header(draw, "功能模块", page_no)
    draw.text((70, 118), "核心模块围绕“模仿成功视频风格”展开。", font=F["h2"], fill=COLORS["ink"])
    draw_wrapped(
        draw,
        "现阶段保留官方稳定的视频生成底座，我们的功能作为电商增强层：更简单的输入、更贴近中文用户的界面、更清晰的素材和配音选择。",
        (74, 178),
        800,
        F["body"],
        COLORS["muted"],
    )

    modules = [
        ("爆款助手", "链接解析、风格提示、AI 改编口播文案"),
        ("素材系统", "本地真实素材 + Pexels/Pixabay 平台素材"),
        ("配音系统", "智能音色库、试听、自定义成品音频"),
        ("成片引擎", "竖屏合成、字幕、背景音乐、批量生成"),
        ("后台配置", "API Key 由运营统一配置，普通用户无需理解模型参数"),
        ("开放接口", "保留官方 API，便于后续接入小程序/桌面端/自动发布"),
    ]
    for idx, (title, body) in enumerate(modules):
        col, row = idx % 2, idx // 2
        x, y = 72 + col * 500, 290 + row * 150
        card(draw, (x, y, x + 430, y + 118), radius=22)
        draw.text((x + 26, y + 24), title, font=F["h4"], fill=COLORS["ink"])
        draw_wrapped(draw, body, (x + 26, y + 62), 360, F["small"], COLORS["muted"], line_gap=8)

    add_image_cover(page, ASSET_DIR / "mobile.png", (1120, 128, 1455, 800), radius=32, crop=True)
    draw.text((1130, 812), "真实 WebUI 截图：移动端/窄屏视图", font=F["tiny"], fill=COLORS["muted"])
    return page


def page_case_food(page_no: int) -> Image.Image:
    page = new_page()
    draw = ImageDraw.Draw(page)
    add_header(draw, "案例一：餐饮门店", page_no)
    draw.text((70, 120), "火锅店新品套餐推广", font=F["h2"], fill=COLORS["ink"])
    draw_wrapped(
        draw,
        "输入一个同城探店或餐饮爆款链接，再补充门店名、套餐卖点和真实菜品素材，系统生成“老板/主播口播 + 菜品特写 + 到店引导”的竖屏短视频。",
        (74, 182),
        820,
        F["body"],
        COLORS["muted"],
        line_gap=12,
    )
    add_image_cover(page, ROOT / "storage/local_videos/1cae78e9-be7c-472e-b587-378eecb40f8a_b75345c8179110f82f1e2a1917134375.jpg", (940, 110, 1510, 500), radius=28)
    add_image_cover(page, ROOT / "storage/local_videos/62980d30-1345-429a-9e48-0897c5cd2171_a659b3adbd57f63dbe300f72c53cc8bd.jpg", (940, 530, 1198, 805), radius=24)
    add_image_cover(page, ROOT / "storage/local_videos/1f0190f6-54ea-4305-a7b7-86b87e049280_1dbbf9de1f396763ff0a381a90b1b424.jpg", (1230, 530, 1510, 805), radius=24)

    sections = [
        ("输入", "爆款链接、门店名称、套餐卖点、真实菜品照片/视频"),
        ("AI 处理", "提炼开场钩子、节奏、镜头风格；自动改写中文口播文案"),
        ("输出", "15-30 秒竖屏宣传片，可用于抖音、小红书、视频号测试"),
    ]
    y = 340
    for title, body in sections:
        card(draw, (76, y, 860, y + 112), radius=20)
        draw.text((104, y + 22), title, font=F["h4"], fill=COLORS["ink"])
        draw_wrapped(draw, body, (220, y + 24), 590, F["small"], COLORS["muted"], line_gap=8)
        y += 136
    return page


def page_case_ecommerce(page_no: int) -> Image.Image:
    page = new_page()
    draw = ImageDraw.Draw(page)
    add_header(draw, "案例二：电商单品", page_no)
    draw.text((70, 120), "从商品卖点到多版本短视频", font=F["h2"], fill=COLORS["ink"])
    draw_wrapped(
        draw,
        "当没有现成爆款链接时，用户可以直接输入商品名、目标人群、优惠信息和使用场景，系统仍能生成文案、关键词和素材检索词。适合电商店铺做 A/B 测试和多平台素材投放。",
        (74, 182),
        1300,
        F["body"],
        COLORS["muted"],
        line_gap=12,
    )
    cards = [
        ("版本 A｜信任介绍", "成熟男声 / 展示参数、场景和售后保障", "适合高客单价商品"),
        ("版本 B｜种草口播", "亲和女声 / 强调痛点、使用前后对比", "适合生活方式商品"),
        ("版本 C｜促销转化", "热情主播 / 强调限时优惠和购买动作", "适合活动期快速放量"),
    ]
    x = 78
    for title, body, tag in cards:
        card(draw, (x, 360, x + 448, 670), radius=26)
        draw.text((x + 28, 396), title, font=F["h3"], fill=COLORS["ink"])
        draw_wrapped(draw, body, (x + 28, 462), 370, F["body"], COLORS["muted"], line_gap=12)
        badge(draw, (x + 28, 590), tag, COLORS["bg2"])
        x += 500

    card(draw, (78, 710, 1520, 800), radius=24, fill=COLORS["dark"])
    draw.text((112, 738), "关键收益：一次商品信息，可以生成多条不同口吻、不同节奏、不同素材组合的视频，方便商家快速测试哪种表达更能转化。", font=F["body_b"], fill=COLORS["white"])
    return page


def page_capability_matrix(page_no: int) -> Image.Image:
    page = new_page()
    draw = ImageDraw.Draw(page)
    add_header(draw, "能力边界与后续扩展", page_no)
    draw.text((70, 120), "现在能稳定测试，后续还能继续增强。", font=F["h2"], fill=COLORS["ink"])

    rows = [
        ("已支持", "爆款链接解析", "公开链接可提取标题/简介/标签，并转成风格提示"),
        ("已支持", "AI 文案改编", "生成口播文案、关键词、发布标题和话题"),
        ("已支持", "视频成片", "本地/平台素材、字幕、配音、背景音乐、竖屏输出"),
        ("已支持", "统一后台配置", "模型、Pexels、TTS 等 API 由运营侧统一维护"),
        ("规划中", "数字人口播", "用老板/主播照片生成开口说话视频，需接入专门视频生成服务"),
        ("规划中", "更强音色克隆", "接入更多商业 TTS 或自建云端声纹服务，扩展方言/情绪"),
    ]
    y = 225
    for status, cap, desc in rows:
        fill = COLORS["bg2"] if status == "已支持" else "#FFF4D6"
        card(draw, (80, y, 1518, y + 82), radius=20)
        badge(draw, (110, y + 22), status, fill)
        draw.text((270, y + 24), cap, font=F["h4"], fill=COLORS["ink"])
        draw_wrapped(draw, desc, (560, y + 25), 850, F["small"], COLORS["muted"], line_gap=8, max_lines=2)
        y += 96
    return page


def page_tech(page_no: int) -> Image.Image:
    page = new_page()
    draw = ImageDraw.Draw(page)
    add_header(draw, "部署与测试状态", page_no)
    draw.text((70, 120), "基于官方稳定底座，增加电商工作流增强层。", font=F["h2"], fill=COLORS["ink"])
    draw_wrapped(
        draw,
        "项目保留 MoneyPrinterTurbo 官方生成能力，前端做中文化和电商流程收敛。API Key 与后台能力由运营统一配置，普通用户只面对必填/可选字段。",
        (74, 182),
        1380,
        F["body"],
        COLORS["muted"],
        line_gap=12,
    )
    items = [
        ("运行形态", "本地 / Docker / 隧道公网测试；后续可接云服务器和对象存储。"),
        ("素材来源", "真实上传素材优先，Pexels/Pixabay 用于补足缺少的画面。"),
        ("配音策略", "默认智能音色库，支持试听和自定义成品录音。"),
        ("质量验证", "已跑通编译、接口、上传、素材检索、TTS、成片与页面检查。"),
    ]
    x, y = 86, 320
    for idx, (title, body) in enumerate(items):
        cx = x + (idx % 2) * 720
        cy = y + (idx // 2) * 180
        card(draw, (cx, cy, cx + 640, cy + 135), radius=24)
        draw.text((cx + 30, cy + 24), title, font=F["h3"], fill=COLORS["ink"])
        draw_wrapped(draw, body, (cx + 30, cy + 78), 560, F["small"], COLORS["muted"], line_gap=8)

    card(draw, (86, 720, 1510, 805), radius=24, fill=COLORS["dark"])
    draw.text((116, 747), "测试结论：核心产品链路已可进行真实 API 与真实素材的整体试用；下一阶段重点是优化数字人、方言音色和公开视频解析稳定性。", font=F["body_b"], fill=COLORS["white"])
    return page


def build_pdf() -> None:
    pages = [
        page_cover_refined(),
        page_positioning(2),
        page_readme_foundation(3),
        page_zaozhao_layer(4),
        page_process_refined(5),
        page_visual_assets(6),
        page_api_readme(7),
        page_case_ecommerce(8),
        page_deployment_readme(9),
        page_capability_matrix(10),
        page_validation_refined(11),
    ]
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(OUT_PDF, save_all=True, append_images=pages[1:], resolution=144.0)
    print(OUT_PDF)


if __name__ == "__main__":
    build_pdf()
