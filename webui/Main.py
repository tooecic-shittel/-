import base64
import copy
import os
import sys
import threading
import time
import webbrowser
from uuid import UUID, uuid4

import streamlit as st
from loguru import logger

# Add the root directory of the project to the system path to allow importing modules from the project
root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)
    print("******** sys.path ********")
    print(sys.path)
    print("")

from app.config import config
from app.models import const
from app.models.schema import (
    MaterialInfo,
    VideoAspect,
    VideoConcatMode,
    VideoParams,
    VideoTransitionMode,
)
from app.services import digital_human, douyin, llm, voice
from app.services import state as sm
from app.services import task as tm
from app.utils import utils

APP_BRAND_NAME = "爪爪IP短视频工作流"
APP_TAGLINE = "提取爆款视频文案和风格，生成真实感老板IP宣传短视频"
logo_file = os.path.join(root_dir, "resource", "public", "zaozhao-logo.svg")
GENERATION_TASK_QUERY_PARAM = "task"

st.set_page_config(
    page_title=APP_BRAND_NAME,
    page_icon=logo_file if os.path.exists(logo_file) else "爪",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        "Report a bug": "https://github.com/harry0703/MoneyPrinterTurbo/issues",
        "About": f"# {APP_BRAND_NAME}\n基于 MoneyPrinterTurbo 的稳定底座，增加老板IP爆款改编助手。",
    },
)


streamlit_style = """
<style>
:root {
    --claw-bg: #f5f7f1;
    --claw-panel: #ffffff;
    --claw-panel-soft: #f9fbf5;
    --claw-ink: #20231f;
    --claw-muted: #6d7468;
    --claw-line: #dfe6d7;
    --claw-line-strong: #ccd7c1;
    --claw-accent: #8FEF26;
    --claw-accent-strong: #6fd817;
    --claw-accent-soft: #eefcdd;
    --claw-radius: 8px;
    --claw-shadow: 0 18px 44px rgba(36, 45, 31, 0.08);
}

.stApp {
    background: var(--claw-bg);
    color: var(--claw-ink);
}

[data-testid="stHeader"] {
    height: 0 !important;
    min-height: 0 !important;
    background: transparent !important;
    pointer-events: none;
}

[data-testid="stToolbar"] {
    display: none;
}

.block-container {
    max-width: 1480px;
    padding-top: 1.85rem;
    padding-bottom: 3.5rem;
}

h1 {
    padding-top: 0 !important;
}

h1, h2, h3, p, label, span, div {
    letter-spacing: 0;
}

.claw-brand-shell {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr);
    gap: 14px;
    align-items: center;
    min-height: 88px;
    margin-top: 0.2rem;
    padding: 18px 20px;
    border: 1px solid var(--claw-line);
    border-radius: var(--claw-radius);
    overflow: visible;
    background:
        linear-gradient(90deg, rgba(143, 239, 38, 0.16), rgba(255, 255, 255, 0.92) 42%),
        var(--claw-panel);
    box-shadow: var(--claw-shadow);
}

.claw-brand-mark {
    width: 50px;
    height: 50px;
    display: grid;
    place-items: center;
    border-radius: var(--claw-radius);
    background: #20231f;
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}

.claw-brand-mark img {
    width: 36px;
    height: 36px;
    display: block;
}

.claw-brand-title {
    margin: 0;
    color: var(--claw-ink);
    font-size: 1.52rem;
    line-height: 1.24;
    font-weight: 780;
    letter-spacing: 0;
}

.claw-brand-subtitle {
    margin-top: 6px;
    color: var(--claw-muted);
    font-size: 0.96rem;
    line-height: 1.45;
}

.claw-brand-badge {
    display: inline-flex;
    align-items: center;
    margin-top: 9px;
    padding: 4px 8px;
    border: 1px solid rgba(143, 239, 38, 0.52);
    border-radius: var(--claw-radius);
    background: rgba(238, 252, 221, 0.74);
    color: #335018;
    font-size: 0.78rem;
    font-weight: 650;
}

.claw-flow {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    margin: 14px 0 12px;
}

.claw-flow-item {
    border: 1px solid var(--claw-line);
    border-radius: var(--claw-radius);
    background: rgba(255, 255, 255, 0.82);
    padding: 10px 12px;
    min-height: 58px;
}

.claw-flow-index {
    color: #335018;
    font-size: 0.76rem;
    font-weight: 760;
}

.claw-flow-title {
    margin-top: 4px;
    color: var(--claw-ink);
    font-size: 0.92rem;
    font-weight: 720;
    line-height: 1.25;
}

.claw-section-title {
    color: var(--claw-ink);
    font-weight: 760;
    font-size: 1.08rem;
    margin-bottom: 4px;
}

.claw-helper-note {
    color: var(--claw-muted);
    font-size: 14px;
    line-height: 1.6;
    margin: -4px 0 12px;
}

.claw-assistant-tip {
    height: 100%;
    min-height: 76px;
    display: flex;
    align-items: center;
    padding: 12px 14px;
    border: 1px solid rgba(143, 239, 38, 0.42);
    border-radius: var(--claw-radius);
    background: rgba(238, 252, 221, 0.58);
    color: #335018;
    font-size: 14px;
    line-height: 1.55;
    font-weight: 620;
}

.claw-pill {
    display: inline-block;
    border: 1px solid rgba(143, 239, 38, 0.52);
    border-radius: var(--claw-radius);
    padding: 4px 9px;
    margin-bottom: 10px;
    color: #335018;
    background: rgba(238, 252, 221, 0.74);
    font-size: 13px;
    font-weight: 650;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--claw-line) !important;
    border-radius: var(--claw-radius) !important;
    background: rgba(255, 255, 255, 0.88) !important;
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.9), 0 12px 30px rgba(36, 45, 31, 0.055);
}

[data-testid="stMarkdownContainer"] p {
    color: var(--claw-muted);
}

[data-testid="stMarkdownContainer"] strong {
    color: var(--claw-ink);
}

label,
label span,
label p,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] *,
[data-testid="stCheckbox"] label,
[data-testid="stCheckbox"] label *,
[data-testid="stRadio"] label,
[data-testid="stRadio"] label *,
[data-testid="stExpander"] label,
[data-testid="stExpander"] label *,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"],
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] span,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] li {
    color: var(--claw-ink) !important;
}

[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] *,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] em,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] small {
    color: var(--claw-muted) !important;
}

[data-testid="stExpander"] [data-testid="stMarkdownContainer"] a,
label a {
    color: #335018 !important;
    font-weight: 680;
}

[data-testid="stTabs"] button,
[data-testid="stTabs"] button *,
[role="tab"],
[role="tab"] * {
    color: var(--claw-ink) !important;
}

[data-testid="stTabs"] button[aria-selected="true"],
[data-testid="stTabs"] button[aria-selected="true"] *,
[role="tab"][aria-selected="true"],
[role="tab"][aria-selected="true"] * {
    color: #335018 !important;
    font-weight: 720 !important;
}

.stTextInput input,
.stTextArea textarea,
[data-baseweb="select"] > div {
    border-color: var(--claw-line) !important;
    border-radius: var(--claw-radius) !important;
    background: #fbfcf8 !important;
    color: var(--claw-ink) !important;
    box-shadow: none !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus,
[data-baseweb="select"] > div:focus-within {
    border-color: var(--claw-accent-strong) !important;
    box-shadow: 0 0 0 3px rgba(143, 239, 38, 0.22) !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #99a192 !important;
}

.stButton > button {
    border-radius: var(--claw-radius) !important;
    border: 1px solid var(--claw-line-strong) !important;
    background: #ffffff !important;
    color: var(--claw-ink) !important;
    font-weight: 680 !important;
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.9);
    transition: transform 120ms ease, border-color 120ms ease, background 120ms ease;
}

.stButton > button [data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
    color: inherit !important;
}

.stButton > button:hover {
    border-color: var(--claw-accent-strong) !important;
    background: var(--claw-accent-soft) !important;
    color: var(--claw-ink) !important;
}

.stButton > button:active {
    transform: translateY(1px);
}

.stButton > button[kind="primary"] {
    border-color: #20231f !important;
    background: #20231f !important;
    color: #ffffff !important;
}

.stButton > button[kind="primary"] [data-testid="stMarkdownContainer"] p {
    color: #ffffff !important;
}

.stButton > button[kind="primary"]:hover {
    border-color: #20231f !important;
    background: #11130f !important;
    color: var(--claw-accent) !important;
}

.stButton > button[kind="primary"]:hover [data-testid="stMarkdownContainer"] p {
    color: var(--claw-accent) !important;
}

.stButton > button:disabled {
    cursor: not-allowed !important;
    opacity: 0.54 !important;
}

[data-testid="stFileUploader"] section {
    border: 1px dashed var(--claw-line-strong) !important;
    border-radius: var(--claw-radius) !important;
    background: #fbfcf8 !important;
}

[data-testid="stAlert"] {
    border-radius: var(--claw-radius) !important;
    border-color: var(--claw-line) !important;
}

details {
    border-radius: var(--claw-radius) !important;
}

hr {
    border-color: var(--claw-line);
}

@media (max-width: 760px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .claw-brand-shell,
    .claw-flow {
        grid-template-columns: 1fr;
    }
    .claw-brand-title {
        font-size: 1.42rem;
    }
}
</style>
"""
st.markdown(streamlit_style, unsafe_allow_html=True)


def localize_streamlit_builtin_text():
    js = """
    <script>
    (function () {
        const targetWindow = parent || window;
        const targetDocument = targetWindow.document;
        const replacements = new Map([
            ["Drag and drop files here", "拖拽文件到这里"],
            ["Drag and drop file here", "拖拽文件到这里"],
            ["Browse files", "选择文件"],
            ["Browse file", "选择文件"],
        ]);

        function translateTextNode(node) {
            let value = node.nodeValue || "";
            const originalValue = value;
            replacements.forEach((zh, en) => {
                value = value.replaceAll(en, zh);
            });
            value = value.replace(/Limit (\\d+\\s*[A-Za-z]+) per file/g, "单个文件最大 $1");
            if (value !== originalValue) {
                node.nodeValue = value;
            }
        }

        function translate(root) {
            if (!root) return;
            const walker = targetDocument.createTreeWalker(
                root,
                4
            );
            while (walker.nextNode()) {
                translateTextNode(walker.currentNode);
            }
            targetDocument
                .querySelectorAll('[data-testid="stFileUploader"] span')
                .forEach((element) => {
                    const text = (element.textContent || "").trim();
                    if (/^Drag and drop files? here$/.test(text)) {
                        element.textContent = "拖拽文件到这里";
                    }
                });
        }

        translate(targetDocument.body);
        const observer = new targetWindow.MutationObserver(() => {
            translate(targetDocument.body);
        });
        observer.observe(targetDocument.body, {
            childList: true,
            subtree: true,
            characterData: true,
        });
        let attempts = 0;
        const timer = targetWindow.setInterval(() => {
            translate(targetDocument.body);
            attempts += 1;
            if (attempts > 30) {
                targetWindow.clearInterval(timer);
            }
        }, 500);
    })();
    </script>
    """
    st.components.v1.html(js, height=0, width=0)


localize_streamlit_builtin_text()

# 定义资源目录
font_dir = os.path.join(root_dir, "resource", "fonts")
song_dir = os.path.join(root_dir, "resource", "songs")
i18n_dir = os.path.join(root_dir, "webui", "i18n")
config_file = os.path.join(root_dir, "webui", ".streamlit", "webui.toml")
system_locale = utils.get_system_locale()


if "video_subject" not in st.session_state:
    st.session_state["video_subject"] = ""
if "video_script" not in st.session_state:
    st.session_state["video_script"] = ""
if "video_terms" not in st.session_state:
    st.session_state["video_terms"] = ""
if "video_script_prompt" not in st.session_state:
    st.session_state["video_script_prompt"] = ""
if "custom_system_prompt" not in st.session_state:
    st.session_state["custom_system_prompt"] = llm.DEFAULT_SCRIPT_SYSTEM_PROMPT
if "use_custom_system_prompt" not in st.session_state:
    st.session_state["use_custom_system_prompt"] = False
if "ui_language" not in st.session_state:
    st.session_state["ui_language"] = config.ui.get("language", system_locale)
if "local_video_materials" not in st.session_state:
    # 记住用户最近一次已经落盘的本地素材，避免仅修改文案后二次生成时丢失素材列表。
    st.session_state["local_video_materials"] = []
if "ecommerce_reference_url" not in st.session_state:
    st.session_state["ecommerce_reference_url"] = ""
if "ecommerce_reference_text" not in st.session_state:
    st.session_state["ecommerce_reference_text"] = ""
if "ecommerce_style_prompt" not in st.session_state:
    st.session_state["ecommerce_style_prompt"] = ""
if "ecommerce_product_name" not in st.session_state:
    st.session_state["ecommerce_product_name"] = ""
if "ecommerce_selling_points" not in st.session_state:
    st.session_state["ecommerce_selling_points"] = ""
if "ecommerce_speaker_role" not in st.session_state:
    st.session_state["ecommerce_speaker_role"] = "老板"

# 加载语言文件。Streamlit 热更新时进程不会重启，清理缓存才能读到新增翻译。
if hasattr(utils.load_locales, "cache_clear"):
    utils.load_locales.cache_clear()
locales = utils.load_locales(i18n_dir)

# 创建一个顶部栏，包含标题和语言选择
title_col, lang_col = st.columns([3, 1])

with title_col:
    logo_html = ""
    if os.path.exists(logo_file):
        with open(logo_file, "rb") as f:
            encoded_logo = base64.b64encode(f.read()).decode("ascii")
        logo_html = f"<img src='data:image/svg+xml;base64,{encoded_logo}' alt='爪爪 logo'>"
    st.markdown(
        f"""
        <div class="claw-brand-shell">
            <div class="claw-brand-mark">{logo_html}</div>
            <div>
                <div class="claw-brand-title">{APP_BRAND_NAME}</div>
                <div class="claw-brand-subtitle">{APP_TAGLINE}</div>
                <div class="claw-brand-badge">基于官方稳定底座 v{config.project_version}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with lang_col:
    display_languages = []
    selected_index = 0
    for i, code in enumerate(locales.keys()):
        display_languages.append(f"{code} - {locales[code].get('Language')}")
        if code == st.session_state.get("ui_language", ""):
            selected_index = i

    selected_language = st.selectbox(
        "Language / 语言",
        options=display_languages,
        index=selected_index,
        key="top_language_selector",
        label_visibility="collapsed",
    )
    if selected_language:
        code = selected_language.split(" - ")[0].strip()
        st.session_state["ui_language"] = code
        config.ui["language"] = code

support_locales = [
    "zh-CN",
    "zh-HK",
    "zh-TW",
    "de-DE",
    "en-US",
    "fr-FR",
    "vi-VN",
    "th-TH",
    "tr-TR",
]


def get_all_fonts():
    fonts = []
    for root, dirs, files in os.walk(font_dir):
        for file in files:
            if file.endswith(".ttf") or file.endswith(".ttc"):
                fonts.append(file)
    fonts.sort()
    return fonts


def get_all_songs():
    songs = []
    for root, dirs, files in os.walk(song_dir):
        for file in files:
            if file.endswith(".mp3"):
                songs.append(file)
    return songs


def open_task_folder(task_id):
    try:
        # task_id 应始终是服务端生成的 UUID。这里先做格式校验，避免异常值
        # 通过路径拼接访问任务目录之外的位置，也避免后续打开目录时触发
        # 平台 shell 对特殊字符的解释。
        normalized_task_id = str(UUID(str(task_id)))
        tasks_root = os.path.abspath(os.path.join(root_dir, "storage", "tasks"))
        path = os.path.abspath(os.path.join(tasks_root, normalized_task_id))

        # 即使 UUID 校验通过，也再次确认最终路径仍在任务根目录内，避免
        # 未来调用方调整 task_id 来源时引入路径穿越风险。
        if not path.startswith(tasks_root + os.sep):
            logger.warning(f"invalid task folder path: {path}")
            return

        if os.path.isdir(path):
            webbrowser.open(f"file://{path}")
    except Exception as e:
        logger.error(e)


def scroll_to_bottom():
    js = """
    <script>
        console.log("scroll_to_bottom");
        function scroll(dummy_var_to_force_repeat_execution){
            var sections = parent.document.querySelectorAll('section.main');
            console.log(sections);
            for(let index = 0; index<sections.length; index++) {
                sections[index].scrollTop = sections[index].scrollHeight;
            }
        }
        scroll(1);
    </script>
    """
    st.components.v1.html(js, height=0, width=0)


def init_log():
    logger.remove()
    _lvl = "DEBUG"

    def format_record(record):
        # 获取日志记录中的文件全路径
        file_path = record["file"].path
        # 将绝对路径转换为相对于项目根目录的路径
        relative_path = os.path.relpath(file_path, root_dir)
        # 更新记录中的文件路径
        record["file"].path = f"./{relative_path}"
        # 返回修改后的格式字符串
        # 您可以根据需要调整这里的格式
        record["message"] = record["message"].replace(root_dir, ".")

        _format = (
            "<green>{time:%Y-%m-%d %H:%M:%S}</> | "
            + "<level>{level}</> | "
            + '"{file.path}:{line}":<blue> {function}</> '
            + "- <level>{message}</>"
            + "\n"
        )
        return _format

    logger.add(
        sys.stdout,
        level=_lvl,
        format=format_record,
        colorize=True,
    )


init_log()

locales = utils.load_locales(i18n_dir)


def tr(key):
    loc = locales.get(st.session_state["ui_language"], {})
    return loc.get("Translation", {}).get(key, key)


st.markdown(
    f"""
    <div class="claw-flow">
        <div class="claw-flow-item">
            <div class="claw-flow-index">01</div>
            <div class="claw-flow-title">{tr("Flow Reference")}</div>
        </div>
        <div class="claw-flow-item">
            <div class="claw-flow-index">02</div>
            <div class="claw-flow-title">{tr("Flow Script")}</div>
        </div>
        <div class="claw-flow-item">
            <div class="claw-flow-index">03</div>
            <div class="claw-flow-title">{tr("Flow Material Voice")}</div>
        </div>
        <div class="claw-flow-item">
            <div class="claw-flow-index">04</div>
            <div class="claw-flow-title">{tr("Flow Generate")}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


admin_mode = False
if hasattr(st, "query_params"):
    configured_admin_token = config.app.get("admin_token", "")
    admin_mode = (
        st.query_params.get("admin", "") == "1"
        and configured_admin_token
        and st.query_params.get("token", "") == configured_admin_token
    )
show_admin_config = admin_mode or config.app.get("show_admin_config", False)


def build_reference_summary(metadata):
    if not metadata:
        return ""
    tags = metadata.get("tags") or []
    tag_text = "、".join(str(tag) for tag in tags[:8] if tag)
    parts = [
        ("标题", metadata.get("title")),
        ("简介", metadata.get("description")),
        ("作者", metadata.get("uploader")),
        ("时长", f"{int(metadata.get('duration'))} 秒" if isinstance(metadata.get("duration"), (int, float)) else ""),
        ("标签", tag_text),
        ("页面", metadata.get("webpage_url") or metadata.get("resolved_url")),
    ]
    return "\n".join(f"{label}：{value}" for label, value in parts if value)


def get_platform_material_source():
    if config.app.get("pexels_api_keys"):
        return "pexels"
    if config.app.get("pixabay_api_keys"):
        return "pixabay"
    preferred_source = config.app.get("video_source", "pexels")
    if preferred_source in ["pexels", "pixabay"]:
        return preferred_source
    return "pexels"


def contains_cjk_text(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text or "")


def normalize_voice_for_script(params: VideoParams):
    if contains_cjk_text(params.video_script or params.video_subject):
        if not params.voice_name or params.voice_name.lower().startswith("en-"):
            params.voice_name = config.app.get(
                "default_tts_voice", "voice-catalog:warm_female"
            )
            config.ui["tts_server"] = "voice-catalog"
            config.ui["voice_name"] = params.voice_name


@st.cache_resource
def get_generation_registry():
    return {
        "lock": threading.Lock(),
        "tasks": {},
        "tasks_by_fingerprint": {},
    }


def build_generation_fingerprint(params: VideoParams) -> str:
    return utils.md5(utils.to_json(params))


def get_task_state(task_id: str):
    if not task_id:
        return None
    return sm.state.get_task(task_id)


def get_generation_task_id_from_query() -> str:
    if not hasattr(st, "query_params"):
        return ""

    task_id = st.query_params.get(GENERATION_TASK_QUERY_PARAM, "")
    if isinstance(task_id, list):
        task_id = task_id[0] if task_id else ""
    task_id = str(task_id or "").strip()
    if not task_id:
        return ""

    try:
        return str(UUID(task_id))
    except (TypeError, ValueError):
        return ""


def remember_generation_task(task_id: str):
    st.session_state["active_generation_task_id"] = task_id
    if hasattr(st, "query_params"):
        st.query_params[GENERATION_TASK_QUERY_PARAM] = task_id


def get_processing_generation_task_ids():
    registry = get_generation_registry()
    with registry["lock"]:
        task_items = sorted(
            registry["tasks"].items(),
            key=lambda item: item[1].get("started_at", 0),
            reverse=True,
        )

    processing_task_ids = []
    for task_id, _ in task_items:
        task_state = get_task_state(task_id)
        if task_state and task_state.get("state") == const.TASK_STATE_PROCESSING:
            processing_task_ids.append(task_id)
    return processing_task_ids


def recover_active_generation_task_id() -> str:
    active_task_id = st.session_state.get("active_generation_task_id", "")
    if active_task_id and get_task_state(active_task_id):
        return active_task_id

    if active_task_id:
        st.session_state.pop("active_generation_task_id", None)

    query_task_id = get_generation_task_id_from_query()
    if query_task_id and get_task_state(query_task_id):
        st.session_state["active_generation_task_id"] = query_task_id
        return query_task_id

    processing_task_ids = get_processing_generation_task_ids()
    if len(processing_task_ids) == 1:
        st.session_state["active_generation_task_id"] = processing_task_ids[0]
        return processing_task_ids[0]

    return ""


def is_task_processing(task_id: str) -> bool:
    task_state = get_task_state(task_id)
    return bool(task_state and task_state.get("state") == const.TASK_STATE_PROCESSING)


def run_generation_task(
    task_id: str, params: VideoParams, fingerprint: str, registry: dict
):
    try:
        result = tm.start(task_id=task_id, params=params)
        with registry["lock"]:
            registry["tasks"].setdefault(task_id, {})["result"] = result
    except Exception as exc:
        logger.exception(f"video generation task crashed: {task_id}")
        sm.state.update_task(
            task_id,
            state=const.TASK_STATE_FAILED,
            progress=0,
            error=str(exc),
        )
        with registry["lock"]:
            registry["tasks"].setdefault(task_id, {})["error"] = str(exc)
    finally:
        with registry["lock"]:
            task_record = registry["tasks"].setdefault(task_id, {})
            task_record["finished_at"] = time.time()
            if registry["tasks_by_fingerprint"].get(fingerprint) == task_id:
                task_state = get_task_state(task_id)
                if task_state and task_state.get("state") == const.TASK_STATE_FAILED:
                    registry["tasks_by_fingerprint"].pop(fingerprint, None)


def start_generation_once(task_id: str, params: VideoParams, fingerprint: str):
    registry = get_generation_registry()
    with registry["lock"]:
        existing_task_id = registry["tasks_by_fingerprint"].get(fingerprint)
        existing_state = get_task_state(existing_task_id) if existing_task_id else None
        if existing_state and existing_state.get("state") in [
            const.TASK_STATE_PROCESSING,
            const.TASK_STATE_COMPLETE,
        ]:
            return existing_task_id, False

        thread = threading.Thread(
            target=run_generation_task,
            args=(task_id, copy.deepcopy(params), fingerprint, registry),
            daemon=True,
        )
        registry["tasks_by_fingerprint"][fingerprint] = task_id
        registry["tasks"][task_id] = {
            "fingerprint": fingerprint,
            "started_at": time.time(),
            "thread": thread,
        }
        thread.start()
        return task_id, True


def render_generation_status(task_id: str, wait: bool = False):
    status_container = st.empty()
    progress_container = st.empty()
    video_container = st.container()

    while True:
        task_state = get_task_state(task_id) or {}
        state_value = task_state.get("state")
        progress_value = int(task_state.get("progress", 0) or 0)
        progress_value = max(0, min(100, progress_value))

        with status_container:
            if state_value == const.TASK_STATE_COMPLETE:
                st.success(tr("Video Generation Completed"))
            elif state_value == const.TASK_STATE_FAILED:
                error_message = task_state.get("error", "")
                st.error(
                    f"{tr('Video Generation Failed')}"
                    + (f"：{error_message}" if error_message else "")
                )
            else:
                st.info(tr("Video Generation In Progress"))

        with progress_container:
            st.progress(progress_value)
            if state_value == const.TASK_STATE_PROCESSING and progress_value >= 50:
                st.caption(tr("Video Combining May Take A While"))

        if state_value == const.TASK_STATE_COMPLETE:
            video_files = task_state.get("videos", [])
            with video_container:
                if video_files:
                    player_cols = st.columns(len(video_files) * 2 + 1)
                    for i, url in enumerate(video_files):
                        player_cols[i * 2 + 1].video(url)
                open_task_folder(task_id)
            if st.session_state.get("active_generation_task_id") == task_id:
                st.session_state.pop("active_generation_task_id", None)
            return True

        if state_value == const.TASK_STATE_FAILED:
            if st.session_state.get("active_generation_task_id") == task_id:
                st.session_state.pop("active_generation_task_id", None)
            return True

        if not wait:
            return False

        time.sleep(2)


def fill_ecommerce_script_fields(
    product_name: str,
    selling_points: str,
    speaker_role: str,
    reference_text: str = "",
    style_prompt: str = "",
    current_script: str = "",
):
    if reference_text or style_prompt or current_script:
        script, used_llm = llm.adapt_reference_video_script(
            reference_text=reference_text,
            style_prompt=style_prompt,
            product_name=product_name,
            selling_points=selling_points,
            speaker_role=speaker_role,
            current_script=current_script,
        )
    else:
        script, used_llm = llm.generate_ecommerce_spokesperson_script(
            product_name=product_name,
            selling_points=selling_points,
            speaker_role=speaker_role,
            style_prompt=style_prompt,
        )

    terms = llm.generate_terms(product_name or selling_points, script)
    st.session_state["video_subject"] = product_name or selling_points
    st.session_state["video_script"] = script
    if isinstance(terms, list):
        st.session_state["video_terms"] = ", ".join(terms)
    elif terms:
        logger.warning(f"failed to fill ecommerce terms: {terms}")

    if style_prompt:
        st.session_state["video_script_prompt"] = (
            tr("Reference Style Prompt Prefix") + "\n\n" + style_prompt
        )

    return used_llm


def render_ecommerce_assistant():
    with st.container(border=True):
        assistant_header_cols = st.columns([2.3, 1])
        with assistant_header_cols[0]:
            st.markdown(
                f'<span class="claw-pill">{tr("New Ecommerce Assistant")}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="claw-section-title">{tr("Ecommerce Viral Assistant")}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="claw-helper-note">{tr("Ecommerce Assistant Help")}</div>',
                unsafe_allow_html=True,
            )
        with assistant_header_cols[1]:
            st.markdown(
                f'<div class="claw-assistant-tip">{tr("Ecommerce Assistant Tip")}</div>',
                unsafe_allow_html=True,
            )

        input_cols = st.columns([1.05, 0.95])
        with input_cols[0]:
            ecommerce_reference_url = st.text_input(
                tr("Reference Video Link Optional"),
                placeholder="https://v.douyin.com/...",
                key="ecommerce_reference_url",
            )
            ecommerce_product_name = st.text_input(
                tr("Product Or Store Required"),
                placeholder=tr("Product Or Store Placeholder"),
                key="ecommerce_product_name",
            )
        with input_cols[1]:
            ecommerce_speaker_role = st.text_input(
                tr("Speaker Role Optional"),
                placeholder=tr("Speaker Role Placeholder"),
                key="ecommerce_speaker_role",
            )
            ecommerce_selling_points = st.text_area(
                tr("Selling Points Required"),
                placeholder=tr("Selling Points Placeholder"),
                height=116,
                key="ecommerce_selling_points",
            )

        extract_col, generate_col, _spacer_col = st.columns([1, 1, 2])
        with extract_col:
            if st.button(tr("Extract Viral Style"), use_container_width=True):
                reference_url = ecommerce_reference_url.strip()
                if not reference_url:
                    st.error(tr("Please Paste Reference Link"))
                else:
                    with st.spinner(tr("Extracting Viral Style")):
                        try:
                            metadata = douyin.extract_video_info(
                                reference_url,
                                download=False,
                                output_dir=utils.storage_dir("douyin", create=True),
                            )
                            reference_text = build_reference_summary(metadata)
                            style_prompt, used_llm = llm.generate_style_prompt_from_video(
                                metadata
                            )
                            st.session_state["ecommerce_reference_text"] = reference_text
                            st.session_state["ecommerce_style_prompt"] = style_prompt
                            st.session_state["video_script_prompt"] = (
                                tr("Reference Style Prompt Prefix")
                                + "\n\n"
                                + style_prompt
                            )
                            product_name = ecommerce_product_name.strip()
                            selling_points = ecommerce_selling_points.strip()
                            speaker_role = (
                                ecommerce_speaker_role.strip()
                                or tr("Default Speaker Role")
                            )
                            if product_name or selling_points:
                                script_used_llm = fill_ecommerce_script_fields(
                                    product_name=product_name,
                                    selling_points=selling_points,
                                    speaker_role=speaker_role,
                                    reference_text=reference_text,
                                    style_prompt=style_prompt,
                                    current_script=st.session_state.get(
                                        "video_script", ""
                                    ).strip(),
                                )
                                st.success(
                                    tr("Script Filled With LLM")
                                    if script_used_llm
                                    else tr("Script Filled With Fallback")
                                )
                            else:
                                st.success(
                                    tr("Style Extracted With LLM")
                                    if used_llm
                                    else tr("Style Extracted With Fallback")
                                )
                                st.info(tr("Please Fill Product Or Selling Points"))
                        except Exception as exc:
                            st.error(f"{tr('Parse Failed')}: {exc}")

        with generate_col:
            if st.button(
                tr("Generate Ecommerce Script"), use_container_width=True, type="primary"
            ):
                product_name = ecommerce_product_name.strip()
                selling_points = ecommerce_selling_points.strip()
                speaker_role = ecommerce_speaker_role.strip() or tr("Default Speaker Role")
                reference_text = st.session_state.get("ecommerce_reference_text", "").strip()
                style_prompt = st.session_state.get("ecommerce_style_prompt", "").strip()
                current_script = st.session_state.get("video_script", "").strip()

                if not product_name and not selling_points:
                    st.error(tr("Please Fill Product Or Selling Points"))
                else:
                    with st.spinner(tr("Generating Ecommerce Script")):
                        used_llm = fill_ecommerce_script_fields(
                            product_name=product_name,
                            selling_points=selling_points,
                            speaker_role=speaker_role,
                            reference_text=reference_text,
                            style_prompt=style_prompt,
                            current_script=current_script,
                        )
                        st.success(
                            tr("Script Filled With LLM")
                            if used_llm
                            else tr("Script Filled With Fallback")
                        )

        with st.expander(tr("Extracted Reference Optional"), expanded=False):
            reference_cols = st.columns(2)
            with reference_cols[0]:
                st.text_area(
                    tr("Reference Video Info"),
                    height=120,
                    key="ecommerce_reference_text",
                )
            with reference_cols[1]:
                st.text_area(
                    tr("Reference Style Prompt"),
                    height=120,
                    key="ecommerce_style_prompt",
                )


# 创建基础设置折叠框
if show_admin_config:
    with st.expander(tr("Basic Settings"), expanded=False):
        config_panels = st.columns(3)
        left_config_panel = config_panels[0]
        middle_config_panel = config_panels[1]
        right_config_panel = config_panels[2]

        # 左侧面板 - 日志设置
        with left_config_panel:
            st.write(tr("Admin Settings"))
            st.info(tr("Admin Settings Help"))
            if st.button(tr("Save Admin Settings"), use_container_width=True):
                config.save_config()
                st.success(tr("Admin Settings Saved"))

            # 是否禁用日志显示
            hide_log = st.checkbox(
                tr("Hide Log"), value=config.ui.get("hide_log", False)
            )
            config.ui["hide_log"] = hide_log

        # 中间面板 - LLM 设置

        with middle_config_panel:
            st.write(tr("LLM Settings"))
            # 下拉框需要展示“AIHubMix（推荐）”这类面向用户的文案，
            # 但配置文件和后端逻辑必须继续使用稳定的小写 provider id。
            # 因此这里显式维护 display label 和 provider id 的映射，避免
            # UI 文案变化污染 `config.app["llm_provider"]`。
            llm_provider_options = [
                ("OpenAI", "openai"),
                ("AIHubMix（推荐）", "aihubmix"),
                ("Moonshot", "moonshot"),
                ("Azure", "azure"),
                ("Qwen", "qwen"),
                ("DeepSeek", "deepseek"),
                ("ModelScope", "modelscope"),
                ("Gemini", "gemini"),
                ("Grok", "grok"),
                ("Ollama", "ollama"),
                ("G4f", "g4f"),
                ("OneAPI", "oneapi"),
                ("Cloudflare", "cloudflare"),
                ("ERNIE", "ernie"),
                ("MiMo", "mimo"),
                ("Pollinations", "pollinations"),
                ("LiteLLM", "litellm"),
            ]
            llm_provider_labels = [label for label, _ in llm_provider_options]
            llm_provider_values = {
                label: provider_id for label, provider_id in llm_provider_options
            }
            saved_llm_provider = config.app.get("llm_provider", "openai").lower()
            saved_llm_provider_index = 0
            for i, (_, provider_id) in enumerate(llm_provider_options):
                if provider_id == saved_llm_provider:
                    saved_llm_provider_index = i
                    break

            llm_provider_label = st.selectbox(
                tr("LLM Provider"),
                options=llm_provider_labels,
                index=saved_llm_provider_index,
            )
            llm_helper = st.container()
            llm_provider = llm_provider_values[llm_provider_label]
            config.app["llm_provider"] = llm_provider

            llm_api_key = config.app.get(f"{llm_provider}_api_key", "")
            llm_secret_key = config.app.get(
                f"{llm_provider}_secret_key", ""
            )  # only for baidu ernie
            llm_base_url = config.app.get(f"{llm_provider}_base_url", "")
            llm_model_name = config.app.get(f"{llm_provider}_model_name", "")
            llm_account_id = config.app.get(f"{llm_provider}_account_id", "")

            tips = ""
            if llm_provider == "ollama":
                if not llm_model_name:
                    llm_model_name = "qwen:7b"
                if not llm_base_url:
                    llm_base_url = config.get_default_ollama_base_url()

                with llm_helper:
                    docker_hint = ""
                    if config.is_running_in_container():
                        docker_hint = "\n                            > 检测到容器环境，未配置 Base Url 时会默认使用 `http://host.docker.internal:11434/v1`\n"
                    tips = f"""
                            ##### Ollama配置说明
                            - **API Key**: 随便填写，比如 123
                            - **Base Url**: 一般为 http://localhost:11434/v1
                                - 如果 `MoneyPrinterTurbo` 和 `Ollama` **不在同一台机器上**，需要填写 `Ollama` 机器的IP地址
                                - 如果 `MoneyPrinterTurbo` 是 `Docker` 部署，建议填写 `http://host.docker.internal:11434/v1`{docker_hint}
                            - **Model Name**: 使用 `ollama list` 查看，比如 `qwen:7b`
                            """

            if llm_provider == "openai":
                if not llm_model_name:
                    llm_model_name = "gpt-3.5-turbo"
                with llm_helper:
                    tips = """
                            ##### OpenAI 配置说明
                            > 需要VPN开启全局流量模式
                            - **API Key**: [点击到官网申请](https://platform.openai.com/api-keys)
                            - **Base Url**: 官方 OpenAI 可留空；如果使用 OpenAI 兼容供应商（例如 OpenRouter），请填写对应的兼容接口地址
                            - **Model Name**: 填写**有权限**的模型；如果使用兼容供应商，请填写该平台支持的模型 ID
                            """

            if llm_provider == "aihubmix":
                if not llm_model_name:
                    llm_model_name = "gpt-5.4-mini"
                if not llm_base_url:
                    llm_base_url = "https://aihubmix.com/v1"
                with llm_helper:
                    tips = """
                            ##### AIHubMix 配置说明
                            - **注册链接**: [点击注册 AIHubMix](https://aihubmix.com/?aff=CEve)
                            - **Base Url**: 预填 https://aihubmix.com/v1
                            - **推荐模型**: 默认 gpt-5.4-mini，也可以填写 AIHubMix 支持的免费模型或其它模型 ID

                            推荐理由：
                            - **模型全**: Claude、GPT、Gemini、Grok、DeepSeek、通义等 700+ 模型一站覆盖
                            - **稳定**: 无限并发，永远在线，集群部署于谷歌云，长期为众多知名应用提供高并发服务
                            - **能力完整**: 文本、图片生成、视频生成、TTS、STT、向量嵌入、Rerank，多模态场景全搞定
                            - **计费透明**: 按量付费，无会员无包月，免费模型可使用
                            """

            if llm_provider == "moonshot":
                if not llm_model_name:
                    llm_model_name = "moonshot-v1-8k"
                with llm_helper:
                    tips = """
                            ##### Moonshot 配置说明
                            - **API Key**: [点击到官网申请](https://platform.moonshot.cn/console/api-keys)
                            - **Base Url**: 固定为 https://api.moonshot.cn/v1
                            - **Model Name**: 比如 moonshot-v1-8k，[点击查看模型列表](https://platform.moonshot.cn/docs/intro#%E6%A8%A1%E5%9E%8B%E5%88%97%E8%A1%A8)
                            """
            if llm_provider == "oneapi":
                if not llm_model_name:
                    llm_model_name = (
                        "claude-3-5-sonnet-20240620"  # 默认模型，可以根据需要调整
                    )
                with llm_helper:
                    tips = """
                        ##### OneAPI 配置说明
                        - **API Key**: 填写您的 OneAPI 密钥
                        - **Base Url**: 填写 OneAPI 的基础 URL
                        - **Model Name**: 填写您要使用的模型名称，例如 claude-3-5-sonnet-20240620
                        """

            if llm_provider == "qwen":
                if not llm_model_name:
                    llm_model_name = "qwen-max"
                with llm_helper:
                    tips = """
                            ##### 通义千问Qwen 配置说明
                            - **API Key**: [点击到官网申请](https://dashscope.console.aliyun.com/apiKey)
                            - **Base Url**: 留空
                            - **Model Name**: 比如 qwen-max，[点击查看模型列表](https://help.aliyun.com/zh/dashscope/developer-reference/model-introduction#3ef6d0bcf91wy)
                            """

            if llm_provider == "g4f":
                if not llm_model_name:
                    llm_model_name = "gpt-3.5-turbo"
                with llm_helper:
                    tips = """
                            ##### gpt4free 配置说明
                            > [GitHub开源项目](https://github.com/xtekky/gpt4free)，可以免费使用GPT模型，但是**稳定性较差**
                            - **API Key**: 随便填写，比如 123
                            - **Base Url**: 留空
                            - **Model Name**: 比如 gpt-3.5-turbo，[点击查看模型列表](https://github.com/xtekky/gpt4free/blob/main/g4f/models.py#L308)
                            """
            if llm_provider == "azure":
                with llm_helper:
                    tips = """
                            ##### Azure 配置说明
                            > [点击查看如何部署模型](https://learn.microsoft.com/zh-cn/azure/ai-services/openai/how-to/create-resource)
                            - **API Key**: [点击到Azure后台创建](https://portal.azure.com/#view/Microsoft_Azure_ProjectOxford/CognitiveServicesHub/~/OpenAI)
                            - **Base Url**: 留空
                            - **Model Name**: 填写你实际的部署名
                            """

            if llm_provider == "gemini":
                if not llm_model_name:
                    llm_model_name = "gemini-1.0-pro"

                with llm_helper:
                    tips = """
                            ##### Gemini 配置说明
                            > 需要VPN开启全局流量模式
                            - **API Key**: [点击到官网申请](https://ai.google.dev/)
                            - **Base Url**: 留空
                            - **Model Name**: 比如 gemini-1.0-pro
                            """

            if llm_provider == "grok":
                if not llm_model_name:
                    llm_model_name = "grok-4.3"
                if not llm_base_url:
                    llm_base_url = "https://api.x.ai/v1"

                with llm_helper:
                    tips = """
                            ##### Grok 配置说明
                            - **API Key**: 填写您的 GrokAPI 密钥
                            - **Base Url**: 填写 GrokAPI 的基础 URL
                            - **Model Name**: 比如 grok-4.3
                            """

            if llm_provider == "deepseek":
                if not llm_model_name:
                    llm_model_name = "deepseek-chat"
                if not llm_base_url:
                    llm_base_url = "https://api.deepseek.com"
                with llm_helper:
                    tips = """
                            ##### DeepSeek 配置说明
                            - **API Key**: [点击到官网申请](https://platform.deepseek.com/api_keys)
                            - **Base Url**: 固定为 https://api.deepseek.com
                            - **Model Name**: 固定为 deepseek-chat
                            """

            if llm_provider == "mimo":
                if not llm_model_name:
                    llm_model_name = "mimo-v2.5-pro"
                if not llm_base_url:
                    llm_base_url = "https://api.xiaomimimo.com/v1"
                with llm_helper:
                    tips = """
                            ##### Xiaomi MiMo 配置说明
                            - **API Key**: [点击到官网申请](https://platform.xiaomimimo.com/docs/zh-CN/quick-start/first-api-call)
                            - **Base Url**: 固定为 https://api.xiaomimimo.com/v1
                            - **Model Name**: 默认 mimo-v2.5-pro，也可以按官方文档填写其它可用模型
                            """

            if llm_provider == "modelscope":
                if not llm_model_name:
                    llm_model_name = "Qwen/Qwen3-32B"
                if not llm_base_url:
                    llm_base_url = "https://api-inference.modelscope.cn/v1/"
                with llm_helper:
                    tips = """
                            ##### ModelScope 配置说明
                            - **API Key**: [点击到官网申请](https://modelscope.cn/docs/model-service/API-Inference/intro)
                            - **Base Url**: 固定为 https://api-inference.modelscope.cn/v1/
                            - **Model Name**: 比如 Qwen/Qwen3-32B，[点击查看模型列表](https://modelscope.cn/models?filter=inference_type&page=1)
                            """

            if llm_provider == "ernie":
                with llm_helper:
                    tips = """
                            ##### 百度文心一言 配置说明
                            - **API Key**: [点击到官网申请](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application)
                            - **Secret Key**: [点击到官网申请](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application)
                            - **Base Url**: 填写 **请求地址** [点击查看文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/jlil56u11#%E8%AF%B7%E6%B1%82%E8%AF%B4%E6%98%8E)
                            """

            if llm_provider == "pollinations":
                if not llm_model_name:
                    llm_model_name = "default"
                with llm_helper:
                    tips = """
                            ##### Pollinations AI Configuration
                            - **API Key**: Optional - Leave empty for public access
                            - **Base Url**: Default is https://text.pollinations.ai/openai
                            - **Model Name**: Use 'openai-fast' or specify a model name
                            """

            if llm_provider == "litellm":
                if not llm_model_name:
                    llm_model_name = "openai/gpt-4o-mini"
                with llm_helper:
                    tips = """
                            ##### LiteLLM Configuration
                            > [LiteLLM](https://github.com/BerriAI/litellm) routes to 100+ LLM providers via a unified interface.
                            > Set your provider's API key as an env var: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `AWS_ACCESS_KEY_ID`, etc.
                            - **Model Name**: LiteLLM format — `openai/gpt-4o`, `anthropic/claude-sonnet-4-20250514`, `bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0`, `gemini/gemini-2.5-flash`. See [full provider list](https://docs.litellm.ai/docs/providers)
                            """

            if tips and config.ui["language"] == "zh":
                # AIHubMix 自身就是 OpenAI-compatible 聚合平台；用户主动选择
                # 该 provider 时，再显示 DeepSeek/Moonshot 的通用推荐会造成
                # 信息干扰，也不利于保持合作入口的轻量、清晰。
                if llm_provider != "aihubmix":
                    st.warning(
                        "中国用户建议使用 **DeepSeek** 或 **Moonshot** 作为大模型提供商\n- 国内可直接访问，不需要VPN \n- 注册就送额度，基本够用"
                    )
                st.info(tips)

            st_llm_api_key = st.text_input(
                tr("API Key"), value=llm_api_key, type="password"
            )
            st_llm_base_url = st.text_input(tr("Base Url"), value=llm_base_url)
            st_llm_model_name = ""
            if llm_provider != "ernie":
                st_llm_model_name = st.text_input(
                    tr("Model Name"),
                    value=llm_model_name,
                    key=f"{llm_provider}_model_name_input",
                )
                if st_llm_model_name:
                    config.app[f"{llm_provider}_model_name"] = st_llm_model_name
            else:
                st_llm_model_name = None

            if st_llm_api_key:
                config.app[f"{llm_provider}_api_key"] = st_llm_api_key
            if st_llm_base_url:
                config.app[f"{llm_provider}_base_url"] = st_llm_base_url
            if st_llm_model_name:
                config.app[f"{llm_provider}_model_name"] = st_llm_model_name
            if llm_provider == "ernie":
                st_llm_secret_key = st.text_input(
                    tr("Secret Key"), value=llm_secret_key, type="password"
                )
                config.app[f"{llm_provider}_secret_key"] = st_llm_secret_key

            if llm_provider == "cloudflare":
                st_llm_account_id = st.text_input(
                    tr("Account ID"), value=llm_account_id
                )
                if st_llm_account_id:
                    config.app[f"{llm_provider}_account_id"] = st_llm_account_id

        # 右侧面板 - API 密钥设置
        with right_config_panel:

            def get_keys_from_config(cfg_key):
                api_keys = config.app.get(cfg_key, [])
                if isinstance(api_keys, str):
                    api_keys = [api_keys]
                api_key = ", ".join(api_keys)
                return api_key

            def save_keys_to_config(cfg_key, value):
                value = value.replace(" ", "")
                if value:
                    config.app[cfg_key] = value.split(",")

            st.write(tr("Video Source Settings"))

            pexels_api_key = get_keys_from_config("pexels_api_keys")
            pexels_api_key = st.text_input(
                tr("Pexels API Key"), value=pexels_api_key, type="password"
            )
            save_keys_to_config("pexels_api_keys", pexels_api_key)

            pixabay_api_key = get_keys_from_config("pixabay_api_keys")
            pixabay_api_key = st.text_input(
                tr("Pixabay API Key"), value=pixabay_api_key, type="password"
            )
            save_keys_to_config("pixabay_api_keys", pixabay_api_key)

            st.divider()
            st.write(tr("Digital Human Settings"))
            digital_human_provider_options = [
                (tr("Digital Human Off"), "none"),
                (tr("Kling Lip Sync"), "kling"),
                (tr("Duix Cloud AIGC"), "duix_cloud"),
                (tr("Duix Local Avatar"), "duix"),
            ]
            saved_digital_human_provider = config.app.get(
                "digital_human_provider", "none"
            )
            provider_values = [item[1] for item in digital_human_provider_options]
            if saved_digital_human_provider not in provider_values:
                saved_digital_human_provider = "none"
            selected_digital_human_provider = st.selectbox(
                tr("Digital Human Provider"),
                options=range(len(digital_human_provider_options)),
                index=provider_values.index(saved_digital_human_provider),
                format_func=lambda x: digital_human_provider_options[x][0],
            )
            config.app["digital_human_provider"] = digital_human_provider_options[
                selected_digital_human_provider
            ][1]
            selected_provider_value = config.app["digital_human_provider"]

            if selected_provider_value == "kling":
                kling_base_url = st.text_input(
                    tr("Kling Base URL"),
                    value=config.app.get(
                        "kling_base_url", "https://api-singapore.klingai.com"
                    ),
                    help=tr("Kling Base URL Help"),
                )
                config.app["kling_base_url"] = kling_base_url.strip()

                kling_access_key = st.text_input(
                    tr("Kling Access Key"),
                    value=config.app.get("kling_access_key", ""),
                    type="password",
                    help=tr("Kling Access Key Help"),
                )
                config.app["kling_access_key"] = kling_access_key.strip()

                kling_secret_key = st.text_input(
                    tr("Kling Secret Key"),
                    value=config.app.get("kling_secret_key", ""),
                    type="password",
                )
                config.app["kling_secret_key"] = kling_secret_key.strip()

                kling_api_key = st.text_input(
                    tr("Kling API Key"),
                    value=config.app.get("kling_api_key", ""),
                    type="password",
                    help=tr("Kling API Key Help"),
                )
                config.app["kling_api_key"] = kling_api_key.strip()

                kling_public_base_url = st.text_input(
                    tr("Kling Public Base URL"),
                    value=config.app.get(
                        "kling_public_base_url",
                        config.app.get("endpoint", ""),
                    ),
                    help=tr("Kling Public Base URL Help"),
                )
                config.app["kling_public_base_url"] = kling_public_base_url.strip()

                kling_path_columns = st.columns(2)
                with kling_path_columns[0]:
                    kling_avatar_path = st.text_input(
                        tr("Kling Avatar Path"),
                        value=config.app.get(
                            "kling_avatar_path",
                            "/v1/videos/avatar/image2video",
                        ),
                    )
                    config.app["kling_avatar_path"] = kling_avatar_path.strip()

                    kling_payload_format = st.selectbox(
                        tr("Kling Payload Format"),
                        options=["avatar", "input", "flat"],
                        index=["avatar", "input", "flat"].index(
                            config.app.get("kling_payload_format", "avatar")
                            if config.app.get("kling_payload_format", "avatar")
                            in ["avatar", "input", "flat"]
                            else "avatar"
                        ),
                        help=tr("Kling Payload Format Help"),
                    )
                    config.app["kling_payload_format"] = kling_payload_format

                with kling_path_columns[1]:
                    kling_query_path_template = st.text_input(
                        tr("Kling Query Path Template"),
                        value=config.app.get("kling_query_path_template", ""),
                        help=tr("Kling Query Path Template Help"),
                    )
                    config.app["kling_query_path_template"] = (
                        kling_query_path_template.strip()
                    )

                    kling_model_name = st.text_input(
                        tr("Kling Model Name"),
                        value=config.app.get("kling_model_name", ""),
                    )
                    config.app["kling_model_name"] = kling_model_name.strip()

                kling_avatar_columns = st.columns(2)
                with kling_avatar_columns[0]:
                    kling_avatar_mode = st.selectbox(
                        tr("Kling Avatar Mode"),
                        options=["std", "pro"],
                        index=0
                        if config.app.get("kling_avatar_mode", "std") == "std"
                        else 1,
                    )
                    config.app["kling_avatar_mode"] = kling_avatar_mode
                with kling_avatar_columns[1]:
                    kling_audio_id = st.text_input(
                        tr("Kling Audio ID"),
                        value=config.app.get("kling_audio_id", ""),
                        help=tr("Kling Audio ID Help"),
                    )
                    config.app["kling_audio_id"] = kling_audio_id.strip()

            elif selected_provider_value == "duix_cloud":
                duix_cloud_base_url = st.text_input(
                    tr("Duix Cloud Base URL"),
                    value=config.app.get("duix_cloud_base_url", "https://meta.guiji.ai"),
                    help=tr("Duix Cloud Base URL Help"),
                )
                config.app["duix_cloud_base_url"] = duix_cloud_base_url.strip()

                duix_cloud_access_key = st.text_input(
                    tr("Duix Cloud Access Key"),
                    value=config.app.get("duix_cloud_access_key", ""),
                    type="password",
                )
                config.app["duix_cloud_access_key"] = duix_cloud_access_key.strip()

                duix_cloud_secret_key = st.text_input(
                    tr("Duix Cloud Secret Key"),
                    value=config.app.get("duix_cloud_secret_key", ""),
                    type="password",
                )
                config.app["duix_cloud_secret_key"] = duix_cloud_secret_key.strip()

                duix_cloud_public_base_url = st.text_input(
                    tr("Duix Cloud Public Base URL"),
                    value=config.app.get(
                        "duix_cloud_public_base_url",
                        config.app.get("endpoint", ""),
                    ),
                    help=tr("Duix Cloud Public Base URL Help"),
                )
                config.app["duix_cloud_public_base_url"] = (
                    duix_cloud_public_base_url.strip()
                )

                duix_cloud_default_scene_id = st.text_input(
                    tr("Duix Cloud Default Scene ID"),
                    value=config.app.get("duix_cloud_default_scene_id", ""),
                    help=tr("Duix Cloud Default Scene ID Help"),
                )
                config.app["duix_cloud_default_scene_id"] = (
                    duix_cloud_default_scene_id.strip()
                )

                duix_cloud_callback_url = st.text_input(
                    tr("Duix Cloud Callback URL"),
                    value=config.app.get("duix_cloud_callback_url", ""),
                    help=tr("Duix Cloud Callback URL Help"),
                )
                config.app["duix_cloud_callback_url"] = duix_cloud_callback_url.strip()

                duix_cloud_render_columns = st.columns(2)
                with duix_cloud_render_columns[0]:
                    duix_cloud_width = st.text_input(
                        tr("Duix Cloud Width"),
                        value=str(config.app.get("duix_cloud_width", "720")),
                    )
                    config.app["duix_cloud_width"] = duix_cloud_width.strip()

                    duix_cloud_fps = st.text_input(
                        tr("Duix Cloud FPS"),
                        value=str(config.app.get("duix_cloud_fps", "25")),
                    )
                    config.app["duix_cloud_fps"] = duix_cloud_fps.strip()

                with duix_cloud_render_columns[1]:
                    duix_cloud_height = st.text_input(
                        tr("Duix Cloud Height"),
                        value=str(config.app.get("duix_cloud_height", "1280")),
                    )
                    config.app["duix_cloud_height"] = duix_cloud_height.strip()

                    duix_cloud_video_format = st.text_input(
                        tr("Duix Cloud Video Format"),
                        value=config.app.get("duix_cloud_video_format", "mp4"),
                    )
                    config.app["duix_cloud_video_format"] = (
                        duix_cloud_video_format.strip()
                    )

            elif selected_provider_value == "duix":
                duix_video_base_url = st.text_input(
                    tr("Duix Video Base URL"),
                    value=config.app.get("duix_video_base_url", "http://127.0.0.1:8383"),
                    help=tr("Duix Video Base URL Help"),
                )
                config.app["duix_video_base_url"] = duix_video_base_url.strip()

                duix_workspace_dir = st.text_input(
                    tr("Duix Workspace Dir"),
                    value=config.app.get(
                        "duix_workspace_dir",
                        "~/duix_avatar_data/face2face/temp",
                    ),
                    help=tr("Duix Workspace Dir Help"),
                )
                config.app["duix_workspace_dir"] = duix_workspace_dir.strip()

                duix_result_dir = st.text_input(
                    tr("Duix Result Dir"),
                    value=config.app.get("duix_result_dir", ""),
                    help=tr("Duix Result Dir Help"),
                )
                config.app["duix_result_dir"] = duix_result_dir.strip()

                config.app["duix_chaofen"] = st.checkbox(
                    tr("Duix HD Mode"),
                    value=bool(config.app.get("duix_chaofen", False)),
                    help=tr("Duix HD Mode Help"),
                )
                config.app["duix_watermark_switch"] = st.checkbox(
                    tr("Duix Watermark"),
                    value=bool(config.app.get("duix_watermark_switch", False)),
                )

llm_provider = config.app.get("llm_provider", "").lower()
params = VideoParams(video_subject="")
uploaded_files = []
uploaded_audio_file = None
uploaded_digital_human_photo = None
uploaded_voice_clone_sample = None

render_ecommerce_assistant()

panel = st.columns(3)
left_panel = panel[0]
middle_panel = panel[1]
right_panel = panel[2]

with left_panel:
    with st.container(border=True):
        st.write(tr("Video Script Settings"))
        params.video_subject = st.text_input(
            tr("Video Subject"),
            key="video_subject",
        ).strip()

        video_languages = [
            (tr("Auto Detect"), ""),
        ]
        for code in support_locales:
            video_languages.append((code, code))

        selected_index = st.selectbox(
            tr("Script Language"),
            index=0,
            options=range(
                len(video_languages)
            ),  # Use the index as the internal option value
            format_func=lambda x: video_languages[x][
                0
            ],  # The label is displayed to the user
        )
        params.video_language = video_languages[selected_index][1]

        with st.expander(tr("Advanced Script Settings"), expanded=False):
            params.paragraph_number = st.slider(
                tr("Script Paragraph Number"),
                min_value=llm.MIN_SCRIPT_PARAGRAPH_NUMBER,
                max_value=llm.MAX_SCRIPT_PARAGRAPH_NUMBER,
                value=st.session_state.get("paragraph_number_input", 1),
                key="paragraph_number_input",
            )
            params.video_script_prompt = st.text_area(
                tr("Custom Script Requirements"),
                height=100,
                max_chars=llm.MAX_SCRIPT_PROMPT_LENGTH,
                placeholder=tr("Custom Script Requirements Placeholder"),
                key="video_script_prompt",
            ).strip()

            use_custom_system_prompt = st.checkbox(
                tr("Use Custom System Prompt"),
                help=tr("Use Custom System Prompt Help"),
                key="use_custom_system_prompt",
            )

            if use_custom_system_prompt:
                custom_system_prompt = st.text_area(
                    tr("Custom System Prompt"),
                    height=240,
                    max_chars=llm.MAX_SCRIPT_SYSTEM_PROMPT_LENGTH,
                    key="custom_system_prompt",
                ).strip()
                params.custom_system_prompt = custom_system_prompt
            else:
                params.custom_system_prompt = ""

        if st.button(
            tr("Generate Video Script and Keywords"), key="auto_generate_script"
        ):
            with st.spinner(tr("Generating Video Script and Keywords")):
                script = llm.generate_script(
                    video_subject=params.video_subject,
                    language=params.video_language,
                    paragraph_number=params.paragraph_number,
                    video_script_prompt=params.video_script_prompt,
                    custom_system_prompt=params.custom_system_prompt,
                )
                terms = llm.generate_terms(params.video_subject, script)
                if "Error: " in script:
                    st.error(tr(script))
                elif "Error: " in terms:
                    st.error(tr(terms))
                else:
                    st.session_state["video_script"] = script
                    st.session_state["video_terms"] = ", ".join(terms)
        params.video_script = st.text_area(
            tr("Video Script"), height=280, key="video_script"
        )
        if st.button(tr("Generate Video Keywords"), key="auto_generate_terms"):
            if not params.video_script:
                st.error(tr("Please Enter the Video Subject"))
                st.stop()

            with st.spinner(tr("Generating Video Keywords")):
                terms = llm.generate_terms(params.video_subject, params.video_script)
                if "Error: " in terms:
                    st.error(tr(terms))
                else:
                    st.session_state["video_terms"] = ", ".join(terms)

        params.video_terms = st.text_area(tr("Video Keywords"), key="video_terms")

with middle_panel:
    with st.container(border=True):
        st.write(tr("Video Settings"))
        params.digital_human_enabled = st.checkbox(
            tr("Enable Digital Human Spokesperson"),
            value=False,
            help=tr("Enable Digital Human Spokesperson Help"),
        )
        if params.digital_human_enabled:
            image_file_types = ["jpg", "jpeg", "png", "webp"]
            video_file_types = ["mp4", "mov", "m4v", "avi", "mkv", "webm"]
            digital_human_file_types = image_file_types + video_file_types
            uploaded_digital_human_photo = st.file_uploader(
                tr("Upload Spokesperson Photo"),
                type=digital_human_file_types
                + [file_type.upper() for file_type in digital_human_file_types],
                accept_multiple_files=False,
                key="digital_human_photo_uploader",
            )
            if uploaded_digital_human_photo:
                file_ext = os.path.splitext(uploaded_digital_human_photo.name)[1].lower()
                if file_ext in [".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"]:
                    st.video(uploaded_digital_human_photo)
                else:
                    st.image(uploaded_digital_human_photo, width=180)
            params.digital_human_provider = config.app.get(
                "digital_human_provider", "none"
            )
            if not digital_human.is_configured():
                st.caption(tr("Digital Human Not Configured Help"))

        video_concat_modes = [
            (tr("Sequential"), "sequential"),
            (tr("Random"), "random"),
        ]
        material_source_modes = [
            (tr("Automatic Material Source"), "auto"),
            (tr("Upload Real Materials"), "local"),
        ]

        saved_video_source_name = config.app.get("video_source", "pexels")
        saved_material_source_mode = (
            "local" if saved_video_source_name == "local" else "auto"
        )
        saved_video_source_index = [v[1] for v in material_source_modes].index(
            saved_material_source_mode
        )

        selected_index = st.selectbox(
            tr("Video Source"),
            options=range(len(material_source_modes)),
            format_func=lambda x: material_source_modes[x][0],
            index=saved_video_source_index,
        )
        selected_material_source = material_source_modes[selected_index][1]
        if selected_material_source == "local":
            params.video_source = "local"
            st.caption(tr("Upload Real Materials Help"))
        else:
            params.video_source = get_platform_material_source()
            st.caption(tr("Automatic Material Source Help"))
        config.app["video_source"] = params.video_source

        if params.video_source == "local":
            # Streamlit 的文件类型校验对扩展名大小写敏感，这里同时放行大小写两种形式。
            local_file_types = ["mp4", "mov", "avi", "flv", "mkv", "jpg", "jpeg", "png"]
            uploaded_files = st.file_uploader(
                tr("Upload Local Materials"),
                type=local_file_types + [file_type.upper() for file_type in local_file_types],
                accept_multiple_files=True,
            )

        selected_index = st.selectbox(
            tr("Video Concat Mode"),
            index=1,
            options=range(
                len(video_concat_modes)
            ),  # Use the index as the internal option value
            format_func=lambda x: video_concat_modes[x][
                0
            ],  # The label is displayed to the user
        )
        params.video_concat_mode = VideoConcatMode(
            video_concat_modes[selected_index][1]
        )

        # 视频转场模式
        video_transition_modes = [
            (tr("None"), VideoTransitionMode.none.value),
            (tr("Shuffle"), VideoTransitionMode.shuffle.value),
            (tr("FadeIn"), VideoTransitionMode.fade_in.value),
            (tr("FadeOut"), VideoTransitionMode.fade_out.value),
            (tr("SlideIn"), VideoTransitionMode.slide_in.value),
            (tr("SlideOut"), VideoTransitionMode.slide_out.value),
        ]
        selected_index = st.selectbox(
            tr("Video Transition Mode"),
            options=range(len(video_transition_modes)),
            format_func=lambda x: video_transition_modes[x][0],
            index=0,
        )
        params.video_transition_mode = VideoTransitionMode(
            video_transition_modes[selected_index][1]
        )

        video_aspect_ratios = [
            (tr("Portrait"), VideoAspect.portrait.value),
            (tr("Landscape"), VideoAspect.landscape.value),
        ]
        selected_index = st.selectbox(
            tr("Video Ratio"),
            options=range(
                len(video_aspect_ratios)
            ),  # Use the index as the internal option value
            format_func=lambda x: video_aspect_ratios[x][
                0
            ],  # The label is displayed to the user
        )
        params.video_aspect = VideoAspect(video_aspect_ratios[selected_index][1])

        params.video_clip_duration = st.selectbox(
            tr("Clip Duration"), options=[2, 3, 4, 5, 6, 7, 8, 9, 10], index=3
        )
        params.video_count = st.selectbox(
            tr("Number of Videos Generated Simultaneously"),
            options=[1, 2, 3, 4, 5],
            index=0,
        )

        with st.expander(tr("Advanced Video Settings"), expanded=False):
            video_codec_options = [
                ("libx264 (CPU)", "libx264"),
                ("NVIDIA NVENC (h264_nvenc)", "h264_nvenc"),
                ("AMD AMF (h264_amf)", "h264_amf"),
                ("Intel QSV (h264_qsv)", "h264_qsv"),
                ("Windows MediaFoundation (h264_mf)", "h264_mf"),
                ("macOS VideoToolbox (h264_videotoolbox)", "h264_videotoolbox"),
            ]
            saved_video_codec = config.app.get("video_codec", "libx264")
            saved_video_codec_values = [item[1] for item in video_codec_options]
            if saved_video_codec not in saved_video_codec_values:
                saved_video_codec = "libx264"
            selected_codec_index = saved_video_codec_values.index(saved_video_codec)
            selected_codec_index = st.selectbox(
                tr("Video Encoder"),
                options=range(len(video_codec_options)),
                index=selected_codec_index,
                format_func=lambda x: video_codec_options[x][0],
                help=tr("Video Encoder Help"),
            )
            config.app["video_codec"] = video_codec_options[selected_codec_index][1]
    with st.container(border=True):
        st.write(tr("Audio Settings"))

        public_tts_servers = [
            ("kling-tts", "可灵 TTS（推荐）"),
            ("voice-catalog", "智能音色库（推荐）"),
        ]
        admin_tts_servers = [
            ("openai-tts", "Audio Speech 备用"),
            ("azure-tts-v1", "Azure TTS V1"),
            ("azure-tts-v2", "Azure TTS V2"),
            ("siliconflow", "SiliconFlow TTS"),
            ("minimax-tts", "MiniMax TTS"),
            ("gemini-tts", "Google Gemini TTS"),
            ("mimo-tts", "Xiaomi MiMo TTS"),
        ]
        tts_servers = (
            public_tts_servers + admin_tts_servers
            if show_admin_config
            else public_tts_servers
        )

        # 获取保存的TTS服务器，默认使用统一音色库。具体供应商由后台路由。
        saved_tts_server = config.ui.get("tts_server", "voice-catalog")
        saved_tts_server_index = 0
        for i, (server_value, _) in enumerate(tts_servers):
            if server_value == saved_tts_server:
                saved_tts_server_index = i
                break

        selected_tts_server_index = st.selectbox(
            tr("TTS Servers"),
            options=range(len(tts_servers)),
            format_func=lambda x: tts_servers[x][1],
            index=saved_tts_server_index,
        )

        selected_tts_server = tts_servers[selected_tts_server_index][0]
        config.ui["tts_server"] = selected_tts_server

        # 根据选择的TTS服务器获取声音列表
        filtered_voices = []

        if selected_tts_server == "voice-catalog":
            filtered_voices = voice.get_voice_catalog_voices()
        elif selected_tts_server == "kling-tts":
            filtered_voices = voice.get_kling_voices()
        elif selected_tts_server == "openai-tts":
            filtered_voices = voice.get_openai_tts_voices()
        elif selected_tts_server == "siliconflow":
            # 获取硅基流动的声音列表
            filtered_voices = voice.get_siliconflow_voices()
        elif selected_tts_server == "minimax-tts":
            filtered_voices = voice.get_minimax_voices()
        elif selected_tts_server == "gemini-tts":
            # 获取Gemini TTS的声音列表
            filtered_voices = voice.get_gemini_voices()
        elif selected_tts_server == "mimo-tts":
            # 获取 Xiaomi MiMo TTS 的预置音色列表
            filtered_voices = voice.get_mimo_voices()
        else:
            # 获取Azure的声音列表
            all_voices = voice.get_all_azure_voices(filter_locals=None)

            # 根据选择的TTS服务器筛选声音
            for v in all_voices:
                if selected_tts_server == "azure-tts-v2":
                    # V2版本的声音名称中包含"v2"
                    if "V2" in v:
                        filtered_voices.append(v)
                else:
                    # V1版本的声音名称中不包含"v2"
                    if "V2" not in v:
                        filtered_voices.append(v)

        friendly_names = {}
        for v in filtered_voices:
            if voice.is_voice_catalog_voice(v):
                friendly_names[v] = voice.get_voice_catalog_label(v)
            elif voice.is_kling_voice(v):
                friendly_names[v] = voice.get_kling_voice_label(v)
            elif voice.is_minimax_voice(v):
                friendly_names[v] = voice.get_minimax_voice_label(v)
            elif voice.is_openai_tts_voice(v):
                friendly_names[v] = voice.get_openai_tts_voice_label(v)
            else:
                friendly_names[v] = (
                    v.replace("Female", tr("Female"))
                    .replace("Male", tr("Male"))
                    .replace("Neural", "")
                )

        saved_voice_name = config.ui.get("voice_name", "")
        saved_voice_name_index = 0

        # 检查保存的声音是否在当前筛选的声音列表中
        if saved_voice_name in friendly_names:
            saved_voice_name_index = list(friendly_names.keys()).index(saved_voice_name)
        else:
            # 如果不在，则根据当前UI语言选择一个默认声音
            for i, v in enumerate(filtered_voices):
                if v.lower().startswith(st.session_state["ui_language"].lower()):
                    saved_voice_name_index = i
                    break

        # 如果没有找到匹配的声音，使用第一个声音
        if saved_voice_name_index >= len(friendly_names) and friendly_names:
            saved_voice_name_index = 0

        # 确保有声音可选
        if friendly_names:
            voice_options_signature = sum(
                sum(ord(ch) for ch in key) for key in friendly_names.keys()
            ) % 100000
            selected_friendly_name = st.selectbox(
                tr("Speech Synthesis"),
                options=list(friendly_names.values()),
                index=min(saved_voice_name_index, len(friendly_names) - 1)
                if friendly_names
                else 0,
                key=(
                    f"speech_synthesis_{selected_tts_server}_"
                    f"{len(friendly_names)}_{voice_options_signature}"
                ),
            )

            voice_name = list(friendly_names.keys())[
                list(friendly_names.values()).index(selected_friendly_name)
            ]
            params.voice_name = voice_name
            config.ui["voice_name"] = voice_name
            if selected_tts_server == "voice-catalog":
                config.app["default_tts_voice"] = voice_name
            elif selected_tts_server == "kling-tts":
                config.app["default_tts_voice"] = voice_name
                config.app["kling_tts_voice_id"] = voice.parse_kling_voice(voice_name)
            elif selected_tts_server == "openai-tts":
                config.app["openai_tts_voice"] = voice_name
        else:
            # 如果没有声音可选，显示提示信息
            st.warning(
                tr(
                    "No voices available for the selected TTS server. Please select another server."
                )
            )
            params.voice_name = ""
            config.ui["voice_name"] = ""

        # 只有在有声音可选时才显示试听按钮
        if friendly_names and st.button(tr("Play Voice")):
            play_content = params.video_subject
            if not play_content:
                play_content = params.video_script
            if not play_content:
                play_content = tr("Voice Example")
            with st.spinner(tr("Synthesizing Voice")):
                temp_dir = utils.storage_dir("temp", create=True)
                audio_file = os.path.join(temp_dir, f"tmp-voice-{str(uuid4())}.mp3")
                sub_maker = voice.tts(
                    text=play_content,
                    voice_name=voice_name,
                    voice_rate=params.voice_rate,
                    voice_file=audio_file,
                    voice_volume=params.voice_volume,
                )
                # if the voice file generation failed, try again with a default content.
                if not sub_maker:
                    play_content = "This is a example voice. if you hear this, the voice synthesis failed with the original content."
                    sub_maker = voice.tts(
                        text=play_content,
                        voice_name=voice_name,
                        voice_rate=params.voice_rate,
                        voice_file=audio_file,
                        voice_volume=params.voice_volume,
                    )

                if sub_maker and os.path.exists(audio_file):
                    st.audio(audio_file, format="audio/mp3")
                    if os.path.exists(audio_file):
                        os.remove(audio_file)

        # 当选择V2版本或者声音是V2声音时，显示服务区域和API key输入框
        if show_admin_config and (
            selected_tts_server == "azure-tts-v2"
            or (voice_name and voice.is_azure_v2_voice(voice_name))
        ):
            saved_azure_speech_region = config.azure.get("speech_region", "")
            saved_azure_speech_key = config.azure.get("speech_key", "")
            azure_speech_region = st.text_input(
                tr("Speech Region"),
                value=saved_azure_speech_region,
                key="azure_speech_region_input",
            )
            azure_speech_key = st.text_input(
                tr("Speech Key"),
                value=saved_azure_speech_key,
                type="password",
                key="azure_speech_key_input",
            )
            config.azure["speech_region"] = azure_speech_region
            config.azure["speech_key"] = azure_speech_key

        # 当选择硅基流动时，显示API key输入框和说明信息
        if show_admin_config and (
            selected_tts_server == "siliconflow"
            or (voice_name and voice.is_siliconflow_voice(voice_name))
        ):
            saved_siliconflow_api_key = config.siliconflow.get("api_key", "")

            siliconflow_api_key = st.text_input(
                tr("SiliconFlow API Key"),
                value=saved_siliconflow_api_key,
                type="password",
                key="siliconflow_api_key_input",
            )

            # 显示硅基流动的说明信息
            st.info(
                tr("SiliconFlow TTS Settings")
                + ":\n"
                + "- "
                + tr("Speed: Range [0.25, 4.0], default is 1.0")
                + "\n"
                + "- "
                + tr("Volume: Uses Speech Volume setting, default 1.0 maps to gain 0")
            )

            config.siliconflow["api_key"] = siliconflow_api_key

        if show_admin_config and (
            selected_tts_server == "minimax-tts"
            or (voice_name and voice.is_minimax_voice(voice_name))
        ):
            saved_minimax_api_key = config.app.get("minimax_api_key", "")

            minimax_api_key = st.text_input(
                "MiniMax API Key",
                value=saved_minimax_api_key,
                type="password",
                key="minimax_tts_api_key_input",
            )

            st.info(
                "MiniMax TTS 会复用 MiniMax API Key，普通用户界面只显示智能音色库。"
            )

            config.app["minimax_api_key"] = minimax_api_key

        # 当选择 Xiaomi MiMo TTS 时，复用 MiMo LLM provider 的 API Key。
        # 这样用户如果同时使用 MiMo 生成文案和语音，只需要维护一份密钥。
        if show_admin_config and (
            selected_tts_server == "mimo-tts"
            or (voice_name and voice.is_mimo_voice(voice_name))
        ):
            saved_mimo_api_key = config.app.get("mimo_api_key", "")

            mimo_api_key = st.text_input(
                tr("MiMo API Key"),
                value=saved_mimo_api_key,
                type="password",
                key="mimo_tts_api_key_input",
            )

            st.info(
                tr("MiMo TTS Settings")
                + ":\n"
                + "- "
                + tr("Uses Xiaomi MiMo V2.5 TTS preset voices")
                + "\n"
                + "- "
                + tr("Speed and volume are currently handled by the provider defaults")
            )

            config.app["mimo_api_key"] = mimo_api_key

        params.voice_volume = st.selectbox(
            tr("Speech Volume"),
            options=[0.6, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0, 4.0, 5.0],
            index=2,
        )

        params.voice_rate = st.selectbox(
            tr("Speech Rate"),
            options=[0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 1.8, 2.0],
            index=2,
        )

        params.voice_clone_enabled = st.checkbox(
            tr("Clone My Voice Optional"),
            value=False,
            help=tr("Clone My Voice Optional Help"),
        )
        if params.voice_clone_enabled:
            voice_sample_file_types = ["mp3", "wav", "m4a", "aac", "flac", "ogg"]
            uploaded_voice_clone_sample = st.file_uploader(
                tr("Upload Voice Sample"),
                type=voice_sample_file_types
                + [file_type.upper() for file_type in voice_sample_file_types],
                accept_multiple_files=False,
                key="voice_clone_sample_uploader",
            )
            if uploaded_voice_clone_sample:
                st.audio(uploaded_voice_clone_sample, format="audio/mp3")
                st.caption(tr("Voice Sample Saved For Clone"))

        custom_audio_file_types = ["mp3", "wav", "m4a", "aac", "flac", "ogg"]
        uploaded_audio_file = st.file_uploader(
            tr("Custom Audio File"),
            type=custom_audio_file_types
            + [file_type.upper() for file_type in custom_audio_file_types],
            accept_multiple_files=False,
            key="custom_audio_file_uploader",
        )
        if uploaded_audio_file:
            st.audio(uploaded_audio_file, format="audio/mp3")
            st.info(
                tr(
                    "Custom audio will be used directly. TTS synthesis will be skipped for this task."
                )
            )

        bgm_options = [
            (tr("No Background Music"), ""),
            (tr("Random Background Music"), "random"),
            (tr("Custom Background Music"), "custom"),
        ]
        selected_index = st.selectbox(
            tr("Background Music"),
            index=1,
            options=range(
                len(bgm_options)
            ),  # Use the index as the internal option value
            format_func=lambda x: bgm_options[x][
                0
            ],  # The label is displayed to the user
        )
        # Get the selected background music type
        params.bgm_type = bgm_options[selected_index][1]

        # Show or hide components based on the selection
        if params.bgm_type == "custom":
            custom_bgm_file = st.text_input(
                tr("Custom Background Music File"), key="custom_bgm_file_input"
            )
            if custom_bgm_file:
                # 这里不直接用 os.path.exists 判断，因为用户常见输入是
                # output000.mp3，这个文件名需要由服务层映射到 resource/songs
                # 目录后再校验。服务层会统一限制目录和文件类型，避免任意路径读取。
                params.bgm_file = custom_bgm_file.strip()
                # st.write(f":red[已选择自定义背景音乐]：**{custom_bgm_file}**")
        params.bgm_volume = st.selectbox(
            tr("Background Music Volume"),
            options=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            index=2,
        )

with right_panel:
    with st.container(border=True):
        st.write(tr("Subtitle Settings"))
        params.subtitle_enabled = st.checkbox(tr("Enable Subtitles"), value=True)
        font_names = get_all_fonts()
        saved_font_name = config.ui.get("font_name", "MicrosoftYaHeiBold.ttc")
        saved_font_name_index = 0
        if saved_font_name in font_names:
            saved_font_name_index = font_names.index(saved_font_name)
        params.font_name = st.selectbox(
            tr("Font"), font_names, index=saved_font_name_index
        )
        config.ui["font_name"] = params.font_name

        subtitle_positions = [
            (tr("Top"), "top"),
            (tr("Center"), "center"),
            (tr("Bottom"), "bottom"),
            (tr("Custom"), "custom"),
        ]
        saved_subtitle_position = config.ui.get("subtitle_position", "bottom")
        saved_position_index = 2
        for i, (_, pos_value) in enumerate(subtitle_positions):
            if pos_value == saved_subtitle_position:
                saved_position_index = i
                break
        selected_index = st.selectbox(
            tr("Position"),
            index=saved_position_index,
            options=range(len(subtitle_positions)),
            format_func=lambda x: subtitle_positions[x][0],
        )
        params.subtitle_position = subtitle_positions[selected_index][1]
        config.ui["subtitle_position"] = params.subtitle_position

        if params.subtitle_position == "custom":
            saved_custom_position = config.ui.get("custom_position", 70.0)
            custom_position = st.text_input(
                tr("Custom Position (% from top)"),
                value=str(saved_custom_position),
                key="custom_position_input",
            )
            try:
                params.custom_position = float(custom_position)
                if params.custom_position < 0 or params.custom_position > 100:
                    st.error(tr("Please enter a value between 0 and 100"))
                else:
                    config.ui["custom_position"] = params.custom_position
            except ValueError:
                st.error(tr("Please enter a valid number"))

        font_cols = st.columns([0.3, 0.7])
        with font_cols[0]:
            saved_text_fore_color = config.ui.get("text_fore_color", "#FFFFFF")
            params.text_fore_color = st.color_picker(
                tr("Font Color"), saved_text_fore_color
            )
            config.ui["text_fore_color"] = params.text_fore_color

        with font_cols[1]:
            saved_font_size = config.ui.get("font_size", 60)
            params.font_size = st.slider(tr("Font Size"), 30, 100, saved_font_size)
            config.ui["font_size"] = params.font_size

        stroke_cols = st.columns([0.3, 0.7])
        with stroke_cols[0]:
            params.stroke_color = st.color_picker(tr("Stroke Color"), "#000000")
        with stroke_cols[1]:
            params.stroke_width = st.slider(tr("Stroke Width"), 0.0, 10.0, 1.5)

        subtitle_bg_cols = st.columns([0.4, 0.6])
        saved_subtitle_background_enabled = config.ui.get(
            "subtitle_background_enabled", True
        )
        with subtitle_bg_cols[0]:
            subtitle_background_enabled = st.checkbox(
                tr("Enable Subtitle Background"),
                value=saved_subtitle_background_enabled,
            )
        config.ui["subtitle_background_enabled"] = subtitle_background_enabled
        if subtitle_background_enabled:
            with subtitle_bg_cols[1]:
                saved_subtitle_background_color = config.ui.get(
                    "subtitle_background_color", "#000000"
                )
                params.text_background_color = st.color_picker(
                    tr("Subtitle Background Color"),
                    saved_subtitle_background_color,
                )
                config.ui["subtitle_background_color"] = params.text_background_color
        else:
            params.text_background_color = False

        saved_rounded_subtitle_background = config.ui.get(
            "rounded_subtitle_background", False
        )
        # 背景关闭时，圆角背景没有可渲染的底色。这里禁用控件并保留原配置，
        # 用户下次重新开启字幕背景后，可以继续使用之前保存的圆角偏好。
        params.rounded_subtitle_background = st.checkbox(
            tr("Rounded Subtitle Background"),
            value=(
                saved_rounded_subtitle_background
                if subtitle_background_enabled
                else False
            ),
            help=tr("Rounded Subtitle Background Help"),
            disabled=not subtitle_background_enabled,
        )
        if subtitle_background_enabled:
            config.ui["rounded_subtitle_background"] = (
                params.rounded_subtitle_background
            )
    if show_admin_config:
        with st.expander(tr("Click to show API Key management"), expanded=False):
            st.subheader(tr("Manage Pexels and Pixabay API Keys"))

            col1, col2 = st.tabs(["Pexels API Keys", "Pixabay API Keys"])

            with col1:
                st.subheader("Pexels API Keys")
                if config.app["pexels_api_keys"]:
                    st.write(tr("Current Keys:"))
                    for key in config.app["pexels_api_keys"]:
                        st.code(key)
                else:
                    st.info(tr("No Pexels API Keys currently"))

                new_key = st.text_input(tr("Add Pexels API Key"), key="pexels_new_key")
                if st.button(tr("Add Pexels API Key")):
                    if new_key and new_key not in config.app["pexels_api_keys"]:
                        config.app["pexels_api_keys"].append(new_key)
                        config.save_config()
                        st.success(tr("Pexels API Key added successfully"))
                    elif new_key in config.app["pexels_api_keys"]:
                        st.warning(tr("This API Key already exists"))
                    else:
                        st.error(tr("Please enter a valid API Key"))

                if config.app["pexels_api_keys"]:
                    delete_key = st.selectbox(
                        tr("Select Pexels API Key to delete"), config.app["pexels_api_keys"], key="pexels_delete_key"
                    )
                    if st.button(tr("Delete Selected Pexels API Key")):
                        config.app["pexels_api_keys"].remove(delete_key)
                        config.save_config()
                        st.success(tr("Pexels API Key deleted successfully"))

            with col2:
                st.subheader("Pixabay API Keys")

                if config.app["pixabay_api_keys"]:
                    st.write(tr("Current Keys:"))
                    for key in config.app["pixabay_api_keys"]:
                        st.code(key)
                else:
                    st.info(tr("No Pixabay API Keys currently"))

                new_key = st.text_input(tr("Add Pixabay API Key"), key="pixabay_new_key")
                if st.button(tr("Add Pixabay API Key")):
                    if new_key and new_key not in config.app["pixabay_api_keys"]:
                        config.app["pixabay_api_keys"].append(new_key)
                        config.save_config()
                        st.success(tr("Pixabay API Key added successfully"))
                    elif new_key in config.app["pixabay_api_keys"]:
                        st.warning(tr("This API Key already exists"))
                    else:
                        st.error(tr("Please enter a valid API Key"))

                if config.app["pixabay_api_keys"]:
                    delete_key = st.selectbox(
                        tr("Select Pixabay API Key to delete"), config.app["pixabay_api_keys"], key="pixabay_delete_key"
                    )
                    if st.button(tr("Delete Selected Pixabay API Key")):
                        config.app["pixabay_api_keys"].remove(delete_key)
                        config.save_config()
                        st.success(tr("Pixabay API Key deleted successfully"))

active_task_id = recover_active_generation_task_id()
active_task_running = is_task_processing(active_task_id)
start_button = st.button(
    tr("Generate Video"),
    use_container_width=True,
    type="primary",
    disabled=active_task_running,
)
if start_button:
    normalize_voice_for_script(params)
    config.save_config()
    task_id = str(uuid4())
    if not params.video_subject and not params.video_script:
        st.error(tr("Video Script and Subject Cannot Both Be Empty"))
        scroll_to_bottom()
        st.stop()

    if params.video_source not in ["pexels", "pixabay", "local"]:
        st.error(tr("Please Select a Valid Video Source"))
        scroll_to_bottom()
        st.stop()

    if params.video_source == "pexels" and not config.app.get("pexels_api_keys", ""):
        st.error(tr("Please Configure Platform Material API Key"))
        scroll_to_bottom()
        st.stop()

    if params.video_source == "pixabay" and not config.app.get("pixabay_api_keys", ""):
        st.error(tr("Please Configure Platform Material API Key"))
        scroll_to_bottom()
        st.stop()

    if params.digital_human_enabled:
        if not uploaded_digital_human_photo:
            st.error(tr("Please Upload Spokesperson Photo"))
            scroll_to_bottom()
            st.stop()
        if not digital_human.is_configured():
            st.error(tr("Please Configure Digital Human Provider"))
            scroll_to_bottom()
            st.stop()

    if uploaded_audio_file:
        task_dir = utils.task_dir(task_id)
        # 上传文件名来自浏览器，不能直接拼到磁盘路径里；这里只保留扩展名，
        # 并使用固定文件名保存到当前任务目录，避免路径穿越或特殊字符问题。
        _, audio_ext = os.path.splitext(os.path.basename(uploaded_audio_file.name))
        audio_ext = audio_ext.lower() or ".mp3"
        custom_audio_path = os.path.join(task_dir, f"custom-audio{audio_ext}")
        with open(custom_audio_path, "wb") as f:
            f.write(uploaded_audio_file.getbuffer())
        params.custom_audio_file = custom_audio_path

    if uploaded_digital_human_photo:
        task_dir = utils.task_dir(task_id)
        _, image_ext = os.path.splitext(os.path.basename(uploaded_digital_human_photo.name))
        image_ext = image_ext.lower() or ".jpg"
        digital_human_photo_path = os.path.join(task_dir, f"digital-human-material{image_ext}")
        with open(digital_human_photo_path, "wb") as f:
            f.write(uploaded_digital_human_photo.getbuffer())
        params.digital_human_photo_file = digital_human_photo_path

    if uploaded_voice_clone_sample:
        task_dir = utils.task_dir(task_id)
        _, sample_ext = os.path.splitext(os.path.basename(uploaded_voice_clone_sample.name))
        sample_ext = sample_ext.lower() or ".mp3"
        voice_clone_sample_path = os.path.join(task_dir, f"voice-clone-sample{sample_ext}")
        with open(voice_clone_sample_path, "wb") as f:
            f.write(uploaded_voice_clone_sample.getbuffer())
        params.voice_clone_sample_file = voice_clone_sample_path

    if uploaded_files:
        local_videos_dir = utils.storage_dir("local_videos", create=True)
        # 每次重新上传时都以本次选择的素材为准，避免旧素材不断重复追加。
        params.video_materials = []
        persisted_local_materials = []
        for file in uploaded_files:
            file_path = os.path.join(local_videos_dir, f"{file.file_id}_{file.name}")
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
                m = MaterialInfo()
                m.provider = "local"
                m.url = file_path
                params.video_materials.append(m)
                persisted_local_materials.append(
                    {
                        "provider": m.provider,
                        "url": m.url,
                        "duration": m.duration,
                    }
                )
        # 将已上传并保存到本地的视频素材写入会话，供后续只改文案时直接复用。
        st.session_state["local_video_materials"] = persisted_local_materials
    elif params.video_source == "local" and st.session_state["local_video_materials"]:
        # 当用户没有重新上传文件时，复用最近一次已经保存到磁盘的本地素材列表。
        params.video_materials = []
        for material in st.session_state["local_video_materials"]:
            m = MaterialInfo()
            m.provider = material.get("provider", "local")
            m.url = material.get("url", "")
            m.duration = material.get("duration", 0)
            if m.url:
                params.video_materials.append(m)

    st.toast(tr("Generating Video"))
    logger.info(tr("Start Generating Video"))
    logger.info(utils.to_json(params))
    scroll_to_bottom()

    fingerprint = build_generation_fingerprint(params)
    task_id, created = start_generation_once(task_id, params, fingerprint)
    remember_generation_task(task_id)
    if not created:
        st.info(tr("Video Generation In Progress"))
    render_generation_status(task_id, wait=True)
    scroll_to_bottom()

elif active_task_id and get_task_state(active_task_id):
    render_generation_status(active_task_id, wait=False)

config.save_config()
