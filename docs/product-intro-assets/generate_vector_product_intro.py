from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
ASSET = ROOT / "docs" / "product-intro-assets"
HTML = ROOT / "docs" / "product-intro-assets" / "爪爪电商短视频工作流_矢量精修版.html"
PDF = ROOT / "docs" / "爪爪电商短视频工作流_产品介绍_矢量精修版.pdf"
PDF_FINAL = ROOT / "docs" / "爪爪电商短视频工作流_产品介绍_最终版.pdf"


def uri(path: Path) -> str:
    return path.resolve().as_uri()


def crop_top(src: Path, dest: Path, top_px: int) -> Path:
    """Create a presentation-safe crop that removes upstream product chrome."""
    with Image.open(src) as image:
        crop = image.crop((0, top_px, image.width, image.height))
        crop.save(dest, quality=94)
    return dest


def write_html() -> None:
    logo_svg = uri(ROOT / "resource/public/zaozhao-logo.svg")
    mobile = uri(ASSET / "mobile.png")
    webui = uri(crop_top(ROOT / "docs/webui.jpg", ASSET / "webui-clean.jpg", 420))
    api = uri(crop_top(ROOT / "docs/api.jpg", ASSET / "api-clean.jpg", 230))
    hotpot = uri(ROOT / "storage/local_videos/1cae78e9-be7c-472e-b587-378eecb40f8a_b75345c8179110f82f1e2a1917134375.jpg")
    beef = uri(ROOT / "storage/local_videos/62980d30-1345-429a-9e48-0897c5cd2171_a659b3adbd57f63dbe300f72c53cc8bd.jpg")
    meat = uri(ROOT / "storage/local_videos/1f0190f6-54ea-4305-a7b7-86b87e049280_1dbbf9de1f396763ff0a381a90b1b424.jpg")

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<title>爪爪电商短视频工作流 产品介绍</title>
<style>
  @page {{ size: 16in 9in; margin: 0; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: #dfe4db;
    color: #172018;
    font-family: "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", Arial, sans-serif;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  .slide {{
    width: 16in;
    height: 9in;
    position: relative;
    overflow: hidden;
    page-break-after: always;
    background: #f7faf2;
  }}
  .slide:last-child {{ page-break-after: auto; }}
  h1, h2, h3, p {{ margin: 0; }}
  .dark {{ background: #0c120e; color: #fff; }}
  .accent {{ color: #82e600; }}
  .muted {{ color: #344133; }}
  .header {{
    position: absolute;
    left: .72in; top: .42in;
    right: .72in;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 15px;
    color: #344133;
  }}
  .header-left {{ display: flex; align-items: center; gap: 12px; font-weight: 700; color: #172018; }}
  .mini-logo {{ width: 34px; height: 34px; border-radius: 9px; background: #0c120e; padding: 6px; }}
  .title-kicker {{
    font-size: 14px; letter-spacing: .16em; text-transform: uppercase; color: #344133; font-weight: 700;
  }}
  .cover-left {{
    position: absolute; left: 0; top: 0; bottom: 0; width: 6.3in;
    background: #0c120e; padding: .78in .74in;
  }}
  .cover-right {{
    position: absolute; left: 6.3in; top: 0; bottom: 0; right: 0;
    background: radial-gradient(circle at 58% 10%, #e6ffd0 0, #e6ffd0 24%, transparent 25%),
                radial-gradient(circle at 82% 92%, #eef7e8 0, #eef7e8 28%, transparent 29%),
                #f7faf2;
  }}
  .brand-title {{ font-size: 30px; line-height: 1.12; font-weight: 900; color: #fff; }}
  .brand-sub {{ margin-top: 8px; font-size: 17px; color: #e7eee1; }}
  .cover-claim {{ margin-top: 1.05in; font-size: 62px; line-height: 1.14; font-weight: 900; letter-spacing: -0.03em; color: #fff; }}
  .cover-copy {{ margin-top: .36in; width: 4.8in; font-size: 22px; line-height: 1.55; color: #f2f7ee; }}
  .pill-grid {{ display: grid; grid-template-columns: repeat(2, max-content); gap: 14px 18px; margin-top: .48in; }}
  .pill {{
    display: inline-flex; height: 38px; align-items: center; padding: 0 18px;
    border: 1.5px solid #37552a; border-radius: 19px; background: #152018;
    color: #defbce; font-size: 17px; font-weight: 800; white-space: nowrap;
  }}
  .date {{ position: absolute; left: .74in; bottom: .54in; font-size: 16px; color: #dbe5d5; }}
  .phone {{
    position: absolute; right: 2.45in; top: .24in; width: 4.85in; height: 8.52in;
    border-radius: .58in; background: #0c120e; padding: .17in; box-shadow: 0 34px 74px rgba(12,18,14,.24);
  }}
  .phone img {{ width: 100%; height: 100%; object-fit: cover; object-position: top; border-radius: .42in; display: block; }}
  .note-card {{
    position: absolute; left: .58in; bottom: 2.08in; width: 3.05in;
    background: #fff; border: 1.5px solid #dde8d3; border-radius: .24in; padding: .28in .32in;
    box-shadow: 0 16px 42px rgba(45,60,40,.08);
  }}
  .note-card h3 {{ font-size: 24px; line-height: 1; margin-bottom: 14px; }}
  .note-card p {{ font-size: 18px; line-height: 1.52; color: #344133; }}
  .main-title {{ position: absolute; left: .78in; top: 1.24in; right: .78in; font-size: 44px; line-height: 1.22; font-weight: 900; letter-spacing: -0.02em; color: #11180f; }}
  .main-title.with-shot {{ right: 8.0in; }}
  .main-title.with-photo {{ right: 6.95in; }}
  .lead {{ position: absolute; left: .8in; top: 2.08in; width: 8.6in; font-size: 22px; line-height: 1.58; color: #344133; }}
  .lead.with-shot {{ width: 6.65in; }}
  .lead.with-photo {{ width: 7.25in; }}
  .card {{
    background: #fff; border: 1.5px solid #dde8d3; border-radius: .24in; padding: .28in;
    box-shadow: 0 10px 30px rgba(45,60,40,.04);
  }}
  .cards-3 {{ position: absolute; left: .78in; right: .78in; top: 3.62in; display: grid; grid-template-columns: repeat(3, 1fr); gap: .38in; }}
  .card h3 {{ font-size: 26px; line-height: 1.15; margin-bottom: 16px; }}
  .card p {{ font-size: 19px; line-height: 1.52; color: #344133; }}
  .metric-row {{ position: absolute; left: .98in; right: .98in; bottom: .82in; display: grid; grid-template-columns: repeat(4, 1fr); gap: .35in; }}
  .metric strong {{ display: block; font-size: 50px; line-height: 1; font-weight: 900; }}
  .metric span {{ display: block; margin-top: 8px; color: #344133; font-size: 17px; }}
  .readme-shot {{ position: absolute; right: .76in; top: 1.08in; width: 6.2in; height: 6.95in; }}
  .shot-frame {{ border: 1.5px solid #dde8d3; border-radius: .24in; overflow: hidden; background: #fff; box-shadow: 0 18px 44px rgba(45,60,40,.08); }}
  .shot-frame img {{ width: 100%; height: 100%; object-fit: cover; object-position: top left; display: block; }}
  .feature-grid {{ position: absolute; left: .8in; top: 3.72in; width: 7.05in; display: grid; grid-template-columns: repeat(3, 1fr); gap: 13px; }}
  .feature {{ background: #fff; border: 1.4px solid #dde8d3; border-radius: 16px; padding: 12px 14px; font-size: 16px; font-weight: 800; white-space: nowrap; }}
  .layer-grid {{ position: absolute; left: .8in; right: .8in; top: 3.02in; display: grid; grid-template-columns: repeat(2, 1fr); gap: .28in .4in; }}
  .layer-card {{ min-height: 1.15in; display: grid; grid-template-columns: 1.35in 1fr; align-items: start; gap: .18in; }}
  .layer-card h3 {{ font-size: 24px; }}
  .layer-card p {{ font-size: 18px; line-height: 1.48; color: #344133; }}
  .dark-callout {{ position: absolute; left: .8in; right: .8in; bottom: .6in; background: #0c120e; color: #fff; border-radius: .22in; padding: .24in .34in; font-size: 23px; font-weight: 800; }}
  .timeline {{ position: absolute; left: .85in; right: .85in; top: 2.35in; display: grid; grid-template-columns: repeat(6, 1fr); gap: .18in; }}
  .step-dot {{ width: .82in; height: .82in; background: #0c120e; border-radius: 50%; color: #82e600; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: 900; margin-bottom: .24in; }}
  .step-card {{ min-height: 2.3in; padding: .2in .18in; }}
  .step-card h3 {{ font-size: 20px; margin-bottom: 12px; }}
  .step-card p {{ font-size: 15px; line-height: 1.48; color: #344133; }}
  .process-callout {{ position: absolute; left: 1.15in; right: 1.15in; bottom: .86in; padding: .32in .42in; background: #fff; border: 1.5px solid #dde8d3; border-radius: .24in; font-size: 27px; font-weight: 900; }}
  .asset-copy {{ position: absolute; left: .8in; top: 3.25in; width: 7.2in; display: grid; gap: .26in; }}
  .asset-row {{ display: grid; grid-template-columns: 1.55in 1fr; gap: .25in; align-items: center; padding: .2in .26in; background: #fff; border: 1.5px solid #dde8d3; border-radius: .22in; }}
  .asset-row h3 {{ font-size: 23px; }}
  .asset-row p {{ font-size: 18px; line-height: 1.46; color: #344133; }}
  .photo-large {{ position: absolute; right: .8in; top: .92in; width: 5.55in; height: 3.7in; border-radius: .24in; overflow: hidden; }}
  .photo-small-a {{ position: absolute; right: 3.75in; top: 5.0in; width: 2.5in; height: 3.0in; border-radius: .2in; overflow: hidden; }}
  .photo-small-b {{ position: absolute; right: .8in; top: 5.0in; width: 2.65in; height: 3.0in; border-radius: .2in; overflow: hidden; }}
  .photo-large img,.photo-small-a img,.photo-small-b img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
  .api-list {{ position: absolute; left: .84in; top: 3.42in; width: 4.45in; display: grid; gap: 10px; }}
  .endpoint {{ background: #fff; border: 1.2px solid #dde8d3; border-radius: 13px; padding: 10px 16px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-weight: 800; color: #172018; }}
  .api-shot {{ position: absolute; right: .78in; top: 1.05in; width: 7.2in; height: 6.85in; }}
  .version-cards {{ position: absolute; left: .78in; right: .78in; top: 3.25in; display: grid; grid-template-columns: repeat(3, 1fr); gap: .38in; }}
  .tag {{ display: inline-flex; margin-top: 22px; background: #eef8e7; border: 1.2px solid #d6e8c9; border-radius: 18px; padding: 8px 14px; font-weight: 800; color: #172018; font-size: 15px; }}
  .matrix {{ position: absolute; left: .8in; right: .8in; top: 2.12in; display: grid; gap: 12px; }}
  .matrix-row {{ display: grid; grid-template-columns: 1.25in 2.35in 1fr; align-items: center; min-height: .72in; background: #fff; border: 1.5px solid #dde8d3; border-radius: .18in; padding: 0 .24in; }}
  .status {{ display: inline-flex; align-items: center; justify-content: center; width: .86in; height: .34in; border-radius: .17in; font-size: 15px; font-weight: 900; background: #eef8e7; }}
  .status.plan {{ background: #fff4d6; }}
  .matrix-row h3 {{ font-size: 21px; }}
  .matrix-row p {{ font-size: 16px; color: #344133; line-height: 1.35; }}
  .check-list {{ position: absolute; left: .95in; top: 4.05in; display: grid; gap: 16px; }}
  .check {{ display: flex; align-items: center; gap: 16px; font-size: 22px; font-weight: 700; }}
  .check i {{ width: 22px; height: 22px; border-radius: 50%; background: #82e600; display: inline-block; }}
  .footer {{ position: absolute; left: .72in; bottom: .38in; font-size: 14px; color: #344133; }}
</style>
</head>
<body>

<section class="slide">
  <div class="cover-left">
    <div class="brand-title">爪爪电商短视频工作流</div>
    <div class="brand-sub">AI commerce video workflow</div>
    <div class="cover-claim">把爆款视频的<br><span class="accent">成功经验</span><br>变成可复用流程</div>
    <p class="cover-copy">面向电商、本地生活和门店老板：参考成功视频，自动生成文案、素材组合、配音、字幕和短视频成片。</p>
    <div class="pill-grid">
      <span class="pill">爆款链接拆解</span><span class="pill">AI 改编文案</span>
      <span class="pill">真实素材优先</span><span class="pill">中文用户友好</span>
    </div>
    <div class="date">产品介绍矢量精修版 · 2026-06-05</div>
  </div>
  <div class="cover-right">
    <div class="phone"><img src="{mobile}" /></div>
  </div>
</section>

<section class="slide">
  <div class="header"><div class="header-left"><img class="mini-logo" src="{logo_svg}" />爪爪电商短视频工作流</div><div>02 · 产品定位</div></div>
  <h2 class="main-title">它解决的不是“做一个视频”，而是“持续复刻有效视频”。</h2>
  <p class="lead">传统工具从空白文案开始，用户要懂脚本、剪辑、配音和素材。爪爪的核心入口改成“参考成功视频”，让用户先给一个爆款链接，再由 AI 提取可迁移的节奏、镜头、卖点表达和口播结构。</p>
  <div class="cards-3">
    <div class="card"><h3>目标用户</h3><p>餐饮门店、探店达人、电商卖家、本地生活商家、短视频代运营团队。</p></div>
    <div class="card"><h3>核心场景</h3><p>新品上架、门店引流、套餐推广、老板/主播口播、批量生成不同风格素材。</p></div>
    <div class="card"><h3>产品价值</h3><p>降低短视频制作门槛，减少从零写文案和找素材的时间，让成功内容经验可复用。</p></div>
  </div>
  <div class="metric-row">
    <div class="metric"><strong>96</strong><span>自动化测试通过</span></div>
    <div class="metric"><strong>9:16</strong><span>默认电商短视频比例</span></div>
    <div class="metric"><strong>29+</strong><span>当前可选智能音色</span></div>
    <div class="metric"><strong>Web/API</strong><span>双入口可扩展</span></div>
  </div>
</section>

<section class="slide">
  <div class="header"><div class="header-left"><img class="mini-logo" src="{logo_svg}" />爪爪电商短视频工作流</div><div>03 · 核心生成能力</div></div>
  <h2 class="main-title with-shot">爪爪提供稳定的视频生成能力。</h2>
  <p class="lead with-shot">用户只需提供视频主题或关键词，系统即可自动生成视频文案、视频素材、字幕、背景音乐，并合成高清短视频。爪爪在此基础上强化电商爆款拆解和中文傻瓜化流程。</p>
  <div class="feature-grid">
    <div class="feature">Web 界面 + API</div><div class="feature">AI 自动文案</div><div class="feature">自定义文案</div>
    <div class="feature">9:16 / 16:9 高清尺寸</div><div class="feature">批量视频生成</div><div class="feature">片段时长设置</div>
    <div class="feature">语音合成试听</div><div class="feature">字幕样式可调</div><div class="feature">背景音乐控制</div>
    <div class="feature">高清素材库</div><div class="feature">本地素材</div><div class="feature">多模型接入</div>
  </div>
  <div class="readme-shot shot-frame"><img src="{webui}" /></div>
</section>

<section class="slide">
  <div class="header"><div class="header-left"><img class="mini-logo" src="{logo_svg}" />爪爪电商短视频工作流</div><div>04 · 爪爪增强层</div></div>
  <h2 class="main-title">我们把复杂的视频生产能力，收敛成电商可用的产品。</h2>
  <p class="lead">用户不需要理解 LLM、TTS、Pexels、字幕或合成参数；运营侧先配置好 API 和默认选项，用户只需要围绕“爆款参考 + 商品卖点 + 真实素材”完成少量输入。</p>
  <div class="layer-grid">
    <div class="card layer-card"><h3>输入收敛</h3><p>商品/店铺名称、卖点、可选爆款链接、可选真实素材。</p></div>
    <div class="card layer-card"><h3>AI 改编</h3><p>提取参考视频的节奏、镜头语言、钩子结构，再改写成自有商品文案。</p></div>
    <div class="card layer-card"><h3>素材策略</h3><p>真实图片/视频优先；不足时用平台素材库补足镜头。</p></div>
    <div class="card layer-card"><h3>配音傻瓜化</h3><p>默认智能音色库，用户只选音色；成品录音可直接上传。</p></div>
    <div class="card layer-card"><h3>中文体验</h3><p>必填/可选清晰标注，减少英文和后台参数暴露。</p></div>
    <div class="card layer-card"><h3>可扩展</h3><p>后续接数字人、方言音色、自动发布和数据反馈。</p></div>
  </div>
  <div class="dark-callout">一句话：生成能力负责“做得出来”，爪爪产品流程负责“让电商用户真的会用、愿意用、反复用”。</div>
</section>

<section class="slide">
  <div class="header"><div class="header-left"><img class="mini-logo" src="{logo_svg}" />爪爪电商短视频工作流</div><div>05 · 端到端流程</div></div>
  <h2 class="main-title">从参考内容到发布素材，形成闭环。</h2>
  <div class="timeline">
    <div><div class="step-dot">1</div><div class="card step-card"><h3>爆款输入</h3><p>粘贴公开视频链接，或直接输入商品信息。</p></div></div>
    <div><div class="step-dot">2</div><div class="card step-card"><h3>风格提取</h3><p>解析标题、简介、标签，AI 总结节奏和镜头语言。</p></div></div>
    <div><div class="step-dot">3</div><div class="card step-card"><h3>文案改编</h3><p>生成电商口播脚本、关键词和发布标题。</p></div></div>
    <div><div class="step-dot">4</div><div class="card step-card"><h3>素材组合</h3><p>真实素材优先，缺镜头再检索平台素材。</p></div></div>
    <div><div class="step-dot">5</div><div class="card step-card"><h3>声音字幕</h3><p>选音色或上传成品录音，生成字幕和 BGM。</p></div></div>
    <div><div class="step-dot">6</div><div class="card step-card"><h3>成片交付</h3><p>输出 9:16 竖屏短视频，可下载和复用。</p></div></div>
  </div>
  <div class="process-callout">对用户来说，只是一个很短的表单；对系统来说，是完整的视频生产流水线。</div>
</section>

<section class="slide">
  <div class="header"><div class="header-left"><img class="mini-logo" src="{logo_svg}" />爪爪电商短视频工作流</div><div>06 · 真实素材策略</div></div>
  <h2 class="main-title with-photo">真实素材决定可信度。</h2>
  <p class="lead with-photo">餐饮、本地生活和电商展示最怕“看起来像假图”。因此产品把本地素材作为第一优先级：老板照片、门店环境、菜品细节、商品包装都可以成为真实感来源。</p>
  <div class="asset-copy">
    <div class="asset-row"><h3>真实素材优先</h3><p>用户上传的菜品、商品、门店、人物素材优先参与合成。</p></div>
    <div class="asset-row"><h3>素材库补充</h3><p>Pexels/Pixabay 负责补足空镜、环境和转场素材。</p></div>
    <div class="asset-row"><h3>可控输出</h3><p>用户可以控制片段时长、拼接模式、字幕样式和背景音乐。</p></div>
  </div>
  <div class="photo-large"><img src="{hotpot}" /></div>
  <div class="photo-small-a"><img src="{beef}" /></div>
  <div class="photo-small-b"><img src="{meat}" /></div>
</section>

<section class="slide">
  <div class="header"><div class="header-left"><img class="mini-logo" src="{logo_svg}" />爪爪电商短视频工作流</div><div>07 · Web + API</div></div>
  <h2 class="main-title with-shot">API 能力适合后续产品化集成。</h2>
  <p class="lead with-shot">平台提供视频生成、字幕生成、音频生成、任务查询、音乐/素材上传、脚本和关键词生成等接口。当前 WebUI 面向普通用户，API 则为后续小程序、桌面端、自动发布和批量任务预留空间。</p>
  <div class="api-list">
    <div class="endpoint">POST /api/v1/videos</div><div class="endpoint">POST /api/v1/subtitle</div><div class="endpoint">POST /api/v1/audio</div>
    <div class="endpoint">GET /api/v1/tasks/{{id}}</div><div class="endpoint">GET /api/v1/musics</div><div class="endpoint">POST /api/v1/scripts</div><div class="endpoint">POST /api/v1/terms</div>
  </div>
  <div class="api-shot shot-frame"><img src="{api}" /></div>
</section>

<section class="slide">
  <div class="header"><div class="header-left"><img class="mini-logo" src="{logo_svg}" />爪爪电商短视频工作流</div><div>08 · 电商单品案例</div></div>
  <h2 class="main-title">一次商品信息，生成多版本短视频。</h2>
  <p class="lead">当没有现成爆款链接时，用户可以直接输入商品名、目标人群、优惠信息和使用场景，系统仍能生成文案、关键词和素材检索词。适合电商店铺做 A/B 测试和多平台素材投放。</p>
  <div class="version-cards">
    <div class="card"><h3>版本 A｜信任介绍</h3><p>成熟男声 / 展示参数、场景和售后保障。</p><span class="tag">适合高客单价商品</span></div>
    <div class="card"><h3>版本 B｜种草口播</h3><p>亲和女声 / 强调痛点、使用前后对比。</p><span class="tag">适合生活方式商品</span></div>
    <div class="card"><h3>版本 C｜促销转化</h3><p>热情主播 / 强调限时优惠和购买动作。</p><span class="tag">适合活动期快速放量</span></div>
  </div>
  <div class="dark-callout">关键收益：同一组商品信息，可以快速测试不同口吻、不同节奏、不同素材组合的视频。</div>
</section>

<section class="slide">
  <div class="header"><div class="header-left"><img class="mini-logo" src="{logo_svg}" />爪爪电商短视频工作流</div><div>09 · 部署与配置</div></div>
  <h2 class="main-title">从本地试用到团队部署，路径清晰。</h2>
  <div class="cards-3" style="top:2.35in;">
    <div class="card"><h3>推荐系统</h3><p>Windows 10+、macOS 11+、主流 Linux。</p></div>
    <div class="card"><h3>最低配置</h3><p>4 核 CPU / 4GB RAM；依赖云端 LLM、TTS 时 GPU 非必须。</p></div>
    <div class="card"><h3>部署方式</h3><p>Windows 一键包、本地 uv、Docker、Google Colab。</p></div>
  </div>
  <div class="cards-3" style="top:5.25in;">
    <div class="card"><h3>关键配置</h3><p>LLM Provider、Pexels/Pixabay、TTS、字幕和素材路径。</p></div>
    <div class="card"><h3>运营策略</h3><p>API Key 统一配置，普通用户无需自行填写。</p></div>
    <div class="card"><h3>扩展路径</h3><p>云端 GPU、对象存储、队列任务、自动发布接口。</p></div>
  </div>
</section>

<section class="slide">
  <div class="header"><div class="header-left"><img class="mini-logo" src="{logo_svg}" />爪爪电商短视频工作流</div><div>10 · 能力边界</div></div>
  <h2 class="main-title">现在能稳定测试，后续还能继续增强。</h2>
  <div class="matrix">
    <div class="matrix-row"><span class="status">已支持</span><h3>爆款链接解析</h3><p>公开链接可提取标题/简介/标签，并转成风格提示。</p></div>
    <div class="matrix-row"><span class="status">已支持</span><h3>AI 文案改编</h3><p>生成口播文案、关键词、发布标题和话题。</p></div>
    <div class="matrix-row"><span class="status">已支持</span><h3>视频成片</h3><p>本地/平台素材、字幕、配音、背景音乐、竖屏输出。</p></div>
    <div class="matrix-row"><span class="status">已支持</span><h3>统一后台配置</h3><p>模型、Pexels、TTS 等 API 由运营侧统一维护。</p></div>
    <div class="matrix-row"><span class="status plan">规划中</span><h3>数字人口播</h3><p>用老板/主播照片生成开口说话视频，需接入专门视频生成服务。</p></div>
    <div class="matrix-row"><span class="status plan">规划中</span><h3>更强音色克隆</h3><p>接入更多商业 TTS 或自建云端声纹服务，扩展方言/情绪。</p></div>
  </div>
</section>

<section class="slide">
  <div class="header"><div class="header-left"><img class="mini-logo" src="{logo_svg}" />爪爪电商短视频工作流</div><div>11 · 测试状态</div></div>
  <h2 class="main-title">核心链路已经可以进入真实 API 试用阶段。</h2>
  <div class="metric-row" style="top:2.3in; bottom:auto;">
    <div class="metric"><strong>96</strong><span>pytest 通过</span></div>
    <div class="metric"><strong>0</strong><span>编译错误</span></div>
    <div class="metric"><strong>29+</strong><span>MiniMax 音色选项</span></div>
    <div class="metric"><strong>PDF</strong><span>矢量文本输出</span></div>
  </div>
  <div class="check-list">
    <div class="check"><i></i>LLM 文案 / 关键词 / 爆款风格 / 发布标题生成通过</div>
    <div class="check"><i></i>MiniMax TTS 抽测通过，旧音色配置具备兜底</div>
    <div class="check"><i></i>Pexels 素材搜索与下载通过</div>
    <div class="check"><i></i>本地素材 + TTS 成片通过</div>
    <div class="check"><i></i>本地素材 + 自定义音频成片通过</div>
    <div class="check"><i></i>上传接口、下载接口、路径安全拦截通过</div>
    <div class="check"><i></i>WebUI 首页和后台入口检查通过</div>
  </div>
  <div class="dark-callout">边界说明：真实抖音链接仍可能受平台风控；数字人口播和更强方言克隆属于下一阶段增强能力。</div>
</section>

</body>
</html>
"""
    HTML.write_text(html, encoding="utf-8")
    print(HTML)
    print(PDF)
    print(PDF_FINAL)


if __name__ == "__main__":
    write_html()
