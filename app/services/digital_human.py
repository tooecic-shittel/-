import hashlib
import ipaddress
import os
import shutil
import subprocess
import time
from typing import Any
from urllib.parse import quote, urlparse

import requests
import jwt
from loguru import logger

from app.config import config
from app.services import video as video_service
from app.utils import utils


_DIGITAL_HUMAN_TIMEOUT_SECONDS = 300
_DUIX_DEFAULT_VIDEO_BASE_URL = "http://127.0.0.1:8383"
_DUIX_DEFAULT_WORKSPACE_DIR = "~/duix_avatar_data/face2face/temp"
_DUIX_CLOUD_DEFAULT_BASE_URL = "https://meta.guiji.ai"
_DUIX_CLOUD_DEFAULT_TIMEOUT_SECONDS = 900
_DUIX_CLOUD_TOKEN_REFRESH_SKEW_SECONDS = 60
_KLING_DEFAULT_BASE_URL = "https://api-singapore.klingai.com"
_KLING_DEFAULT_TIMEOUT_SECONDS = 900
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
_VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
_LOCAL_URL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
_duix_cloud_token_cache: dict[str, Any] = {
    "access_token": "",
    "expires_at": 0.0,
}


def is_configured() -> bool:
    provider = _get_provider()
    if provider == "duix":
        return bool(_duix_video_base_url())
    if provider == "duix_cloud":
        return bool(_duix_cloud_access_key() and _duix_cloud_secret_key())
    if provider == "kling":
        return bool(_kling_access_key() and _kling_secret_key()) or bool(
            _kling_api_key()
        )
    return False


def generate(
    task_id: str,
    photo_file: str,
    audio_file: str,
    script_text: str = "",
) -> str:
    provider = _get_provider()
    if provider in ("", "none", "off"):
        logger.info("digital human provider is disabled")
        return ""

    if not photo_file:
        logger.info("digital human spokesperson material is not provided")
        return ""

    if not audio_file or not os.path.exists(audio_file):
        logger.warning(f"digital human audio file is missing: {audio_file}")
        return ""

    if provider == "duix":
        return _generate_with_duix(
            task_id=task_id,
            avatar_file=photo_file,
            audio_file=audio_file,
            script_text=script_text,
        )
    if provider == "duix_cloud":
        return _generate_with_duix_cloud(
            task_id=task_id,
            avatar_file=photo_file,
            audio_file=audio_file,
            script_text=script_text,
        )
    if provider == "kling":
        return _generate_with_kling(
            task_id=task_id,
            avatar_file=photo_file,
            audio_file=audio_file,
            script_text=script_text,
        )

    logger.warning(f"unsupported digital human provider: {provider}")
    return ""


def _get_provider() -> str:
    return str(config.app.get("digital_human_provider", "none") or "none").strip().lower()


def _duix_video_base_url() -> str:
    return str(
        config.app.get("duix_video_base_url", "") or _DUIX_DEFAULT_VIDEO_BASE_URL
    ).strip().rstrip("/")


def _duix_workspace_dir() -> str:
    workspace_dir = str(
        config.app.get("duix_workspace_dir", "")
        or config.app.get("duix_face2face_dir", "")
        or _DUIX_DEFAULT_WORKSPACE_DIR
    ).strip()
    return os.path.abspath(os.path.expanduser(workspace_dir))


def _duix_result_dir() -> str:
    result_dir = str(config.app.get("duix_result_dir", "") or "").strip()
    if not result_dir:
        return _duix_workspace_dir()
    return os.path.abspath(os.path.expanduser(result_dir))


def _duix_endpoint(path: str) -> str:
    base_url = _duix_video_base_url()
    if base_url.endswith("/easy"):
        base_url = base_url[: -len("/easy")]
    return f"{base_url}/easy/{path.lstrip('/')}"


def _copy_to_duix_workspace(source_file: str, task_id: str, name: str) -> str:
    workspace_dir = _duix_workspace_dir()
    os.makedirs(workspace_dir, exist_ok=True)
    ext = os.path.splitext(source_file)[1].lower() or ".bin"
    target_name = f"claw-{task_id}-{name}{ext}"
    target_path = os.path.join(workspace_dir, target_name)
    if os.path.abspath(source_file) != os.path.abspath(target_path):
        shutil.copyfile(source_file, target_path)
    return target_name


def _is_image_file(file_path: str) -> bool:
    return os.path.splitext(file_path)[1].lower() in _IMAGE_EXTENSIONS


def _is_video_file(file_path: str) -> bool:
    return os.path.splitext(file_path)[1].lower() in _VIDEO_EXTENSIONS


def _make_video_from_image(image_file: str, task_id: str) -> str:
    task_dir = utils.task_dir(task_id)
    output_file = os.path.join(task_dir, "digital-human-avatar.mp4")
    duration = float(config.app.get("duix_image_video_duration", 5) or 5)
    fps = int(config.app.get("duix_image_video_fps", 25) or 25)
    ffmpeg_binary = video_service.get_ffmpeg_binary()
    command = [
        ffmpeg_binary,
        "-y",
        "-loop",
        "1",
        "-i",
        image_file,
        "-t",
        str(duration),
        "-r",
        str(fps),
        "-vf",
        "scale=720:-2,format=yuv420p",
        "-an",
        output_file,
    ]
    logger.info("converting spokesperson image to a short avatar video for Duix")
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except Exception as exc:
        logger.warning(f"failed to convert image to avatar video: {str(exc)}")
        return ""
    return output_file


def _prepare_duix_avatar_file(task_id: str, avatar_file: str) -> str:
    if not os.path.exists(avatar_file):
        logger.warning(f"digital human spokesperson file is missing: {avatar_file}")
        return ""

    if _is_video_file(avatar_file):
        return avatar_file

    if _is_image_file(avatar_file):
        converted_video = _make_video_from_image(avatar_file, task_id)
        if converted_video:
            return converted_video
        logger.warning("Duix needs a spokesperson video; image conversion failed")
        return ""

    logger.warning(f"unsupported digital human material type: {avatar_file}")
    return ""


def _generate_with_duix(
    task_id: str,
    avatar_file: str,
    audio_file: str,
    script_text: str = "",
) -> str:
    prepared_avatar_file = _prepare_duix_avatar_file(task_id, avatar_file)
    if not prepared_avatar_file:
        return ""

    try:
        video_ref = _copy_to_duix_workspace(prepared_avatar_file, task_id, "avatar")
        audio_ref = _copy_to_duix_workspace(audio_file, task_id, "audio")
    except Exception as exc:
        logger.warning(f"failed to prepare Duix workspace files: {str(exc)}")
        return ""

    job_code = f"claw-{task_id}"
    payload = {
        "audio_url": audio_ref,
        "video_url": video_ref,
        "code": job_code,
        "chaofen": bool(config.app.get("duix_chaofen", False)),
        "watermark_switch": bool(config.app.get("duix_watermark_switch", False)),
        "pn": str(config.app.get("duix_project_name", "") or "claw-ecommerce"),
    }
    if script_text:
        payload["text"] = script_text[:500]

    logger.info("creating Duix digital human video")
    try:
        response = requests.post(
            _duix_endpoint("submit"),
            json=payload,
            timeout=30,
            verify=config.app.get("tls_verify", True),
        )
    except Exception as exc:
        logger.warning(f"failed to submit Duix digital human task: {str(exc)}")
        return ""

    if response.status_code >= 400:
        logger.warning(f"Duix submit failed: {response.status_code}, {response.text}")
        return ""

    submit_data = _safe_json(response)
    if submit_data and submit_data.get("code") not in (None, 10000, "10000"):
        logger.warning(f"Duix submit returned an error: {submit_data}")
        return ""

    result_ref = _wait_for_duix_result(job_code)
    if not result_ref:
        return ""

    output_file = os.path.join(utils.task_dir(task_id), "digital-human.mp4")
    if not _copy_or_download_duix_result(result_ref, output_file):
        return ""
    return output_file


def _config_str(key: str, default: str = "") -> str:
    return str(config.app.get(key, default) or default).strip()


def _duix_cloud_base_url() -> str:
    return _config_str("duix_cloud_base_url", _DUIX_CLOUD_DEFAULT_BASE_URL).rstrip("/")


def _duix_cloud_access_key() -> str:
    return _config_str("duix_cloud_access_key")


def _duix_cloud_secret_key() -> str:
    return _config_str("duix_cloud_secret_key")


def _duix_cloud_endpoint(path: str) -> str:
    return f"{_duix_cloud_base_url()}/{path.lstrip('/')}"


def _duix_cloud_request_timeout() -> int:
    return max(5, int(config.app.get("duix_cloud_request_timeout", 30) or 30))


def _duix_cloud_get_token() -> str:
    cached_token = _duix_cloud_token_cache.get("access_token", "")
    expires_at = float(_duix_cloud_token_cache.get("expires_at", 0) or 0)
    if cached_token and time.time() < expires_at:
        return str(cached_token)

    access_key = _duix_cloud_access_key()
    secret_key = _duix_cloud_secret_key()
    if not access_key or not secret_key:
        logger.warning("Duix cloud access key or secret key is not configured")
        return ""

    timestamp = str(int(time.time() * 1000))
    sign = hashlib.md5(f"{access_key}{timestamp}{secret_key}".encode("utf-8")).hexdigest()
    params = {
        "grant_type": "sign",
        "timestamp": timestamp,
        "sign": sign,
        "appId": access_key,
    }

    try:
        response = requests.get(
            _duix_cloud_endpoint("/openapi/oauth/token"),
            params=params,
            timeout=_duix_cloud_request_timeout(),
            verify=config.app.get("tls_verify", True),
        )
    except Exception as exc:
        logger.warning(f"failed to request Duix cloud token: {str(exc)}")
        return ""

    if response.status_code >= 400:
        logger.warning(f"Duix cloud token request failed: {response.status_code}")
        return ""

    data = _safe_json(response)
    if not _duix_cloud_success(data):
        logger.warning(
            f"Duix cloud token request returned an error: "
            f"{data.get('code')} {data.get('message', '')}"
        )
        return ""

    token_data = data.get("data") or {}
    access_token = token_data.get("access_token") or token_data.get("accessToken")
    if not access_token:
        logger.warning("Duix cloud token response did not include access_token")
        return ""

    expires_in = int(token_data.get("expires_in") or token_data.get("expiresIn") or 7200)
    _duix_cloud_token_cache["access_token"] = str(access_token)
    _duix_cloud_token_cache["expires_at"] = (
        time.time()
        + max(60, expires_in - _DUIX_CLOUD_TOKEN_REFRESH_SKEW_SECONDS)
    )
    return str(access_token)


def _duix_cloud_success(data: dict) -> bool:
    if not isinstance(data, dict):
        return False
    code = data.get("code")
    if code is None:
        return data.get("success") is True and "data" in data
    if code not in (0, "0"):
        return False
    if data.get("success") is False:
        return False
    return True


def _duix_cloud_request(
    method: str,
    path: str,
    payload: dict | None = None,
    timeout: int | None = None,
) -> dict:
    access_token = _duix_cloud_get_token()
    if not access_token:
        return {}

    request_timeout = timeout or _duix_cloud_request_timeout()
    try:
        response = requests.request(
            method=method,
            url=_duix_cloud_endpoint(path),
            params={"access_token": access_token},
            json=payload,
            timeout=request_timeout,
            verify=config.app.get("tls_verify", True),
        )
    except Exception as exc:
        logger.warning(f"failed to request Duix cloud {path}: {str(exc)}")
        return {}

    if response.status_code >= 400:
        logger.warning(f"Duix cloud {path} failed: {response.status_code}")
        return {}

    data = _safe_json(response)
    if not _duix_cloud_success(data):
        logger.warning(
            f"Duix cloud {path} returned an error: "
            f"{data.get('code')} {data.get('message', '')}"
        )
        return {}
    return data


def _duix_cloud_public_base_url() -> str:
    return (
        _config_str("duix_cloud_public_base_url")
        or _config_str("endpoint")
    ).rstrip("/")


def _duix_cloud_url_is_allowed(url: str) -> bool:
    if config.app.get("duix_cloud_allow_local_urls", False):
        return True

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").strip().lower()
    if not hostname:
        return False
    if hostname in _LOCAL_URL_HOSTS:
        return False

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        return True
    return not (ip.is_loopback or ip.is_private or ip.is_link_local)


def _duix_cloud_file_url(file_path: str, purpose: str) -> str:
    if _looks_like_url(file_path):
        return file_path

    if not file_path or not os.path.exists(file_path):
        logger.warning(f"Duix cloud {purpose} file does not exist")
        return ""

    public_base_url = _duix_cloud_public_base_url()
    if not public_base_url:
        logger.warning(
            "Duix cloud needs duix_cloud_public_base_url or endpoint to expose "
            f"the {purpose} file as a public URL"
        )
        return ""

    if not _duix_cloud_url_is_allowed(public_base_url):
        logger.warning(
            "Duix cloud public base URL must be reachable from the public internet; "
            "localhost or private network URLs are not accepted by default"
        )
        return ""

    tasks_root = os.path.abspath(utils.task_dir())
    resolved_path = os.path.abspath(file_path)
    if not resolved_path.startswith(tasks_root + os.sep):
        logger.warning(f"Duix cloud {purpose} file is not under the task storage dir")
        return ""

    relative_path = os.path.relpath(resolved_path, tasks_root).replace(os.sep, "/")
    return f"{public_base_url.rstrip('/')}/tasks/{quote(relative_path, safe='/')}"


def _duix_cloud_build_video_payload(
    scene_id: str,
    audio_url: str,
    task_id: str,
) -> dict:
    payload = {
        "audioUrl": audio_url,
        "sceneId": str(scene_id),
        "videoName": _config_str(
            "duix_cloud_video_name",
            f"claw-ecommerce-{task_id[:8]}",
        ),
    }
    optional_fields = {
        "backgroundUrl": "duix_cloud_background_url",
        "callbackUrl": "duix_cloud_callback_url",
        "bitRate": "duix_cloud_bit_rate",
        "width": "duix_cloud_width",
        "height": "duix_cloud_height",
        "mask": "duix_cloud_mask",
        "fps": "duix_cloud_fps",
        "matting": "duix_cloud_matting",
        "pixFmt": "duix_cloud_pix_fmt",
        "videoFormat": "duix_cloud_video_format",
    }
    for payload_key, config_key in optional_fields.items():
        value = _config_str(config_key)
        if value:
            payload[payload_key] = value

    return payload


def _duix_cloud_submit_training(task_id: str, avatar_file: str) -> str:
    if not _is_video_file(avatar_file):
        logger.warning(
            "Duix cloud training currently requires a spokesperson video URL; "
            "photo-only material should use a pre-trained sceneId or another provider"
        )
        return ""

    video_url = _duix_cloud_file_url(avatar_file, "training video")
    if not video_url:
        return ""

    payload = {
        "name": _config_str(
            "duix_cloud_training_name",
            f"claw-spokesperson-{task_id[:8]}",
        ),
        "videoUrl": video_url,
    }

    callback_url = (
        _config_str("duix_cloud_training_callback_url")
        or _config_str("duix_cloud_callback_url")
    )
    if callback_url:
        payload["callbackUrl"] = callback_url

    training_level = _config_str("duix_cloud_training_level")
    if training_level:
        payload["level"] = training_level

    green_screen = _config_str("duix_cloud_training_green_screen")
    if green_screen:
        payload["greenScreen"] = green_screen

    data = _duix_cloud_request(
        "POST",
        "/openapi/video/v2/create/training",
        payload=payload,
    )
    training_data = data.get("data") or {}
    training_id = training_data.get("trainingId") or training_data.get("id")
    if not training_id:
        logger.warning("Duix cloud training response did not include trainingId")
        return ""

    logger.info(f"Duix cloud training task submitted: {training_id}")
    return str(training_id)


def _duix_cloud_wait_for_training(training_id: str) -> str:
    timeout = int(
        config.app.get("duix_cloud_training_timeout", _DUIX_CLOUD_DEFAULT_TIMEOUT_SECONDS)
        or _DUIX_CLOUD_DEFAULT_TIMEOUT_SECONDS
    )
    poll_interval = max(
        5, int(config.app.get("duix_cloud_poll_interval", 5) or 5)
    )
    deadline = time.time() + timeout

    while time.time() < deadline:
        data = _duix_cloud_request(
            "GET",
            f"/openapi/video/v2/training/get/{training_id}",
        )
        task_data = data.get("data") or {}
        status = task_data.get("status")
        status_text = str(status).strip()

        if status_text == "2":
            scene_id = task_data.get("sceneId")
            if not scene_id:
                scene_id = _duix_cloud_scene_id_from_robot(task_data.get("robot"))
            if scene_id:
                logger.success("Duix cloud training is ready")
                return str(scene_id)
            logger.warning("Duix cloud training succeeded without sceneId")
            return ""

        if status_text in {"3", "4"}:
            logger.warning(
                f"Duix cloud training failed: status={status_text}, "
                f"comment={task_data.get('comment', '')}"
            )
            return ""

        logger.info(f"Duix cloud training status: {status_text or 'pending'}")
        time.sleep(poll_interval)

    logger.warning(f"Duix cloud training timed out after {timeout}s")
    return ""


def _duix_cloud_scene_id_from_robot(robot_data: Any) -> str:
    if not isinstance(robot_data, dict):
        return ""
    scene = robot_data.get("scene")
    if isinstance(scene, dict) and scene.get("id"):
        return str(scene["id"])
    scene_list = robot_data.get("sceneList")
    if isinstance(scene_list, list):
        for item in scene_list:
            if isinstance(item, dict) and item.get("id"):
                return str(item["id"])
    return ""


def _duix_cloud_create_audio_video(
    task_id: str,
    scene_id: str,
    audio_file: str,
) -> str:
    audio_url = _duix_cloud_file_url(audio_file, "audio")
    if not audio_url:
        return ""

    data = _duix_cloud_request(
        "POST",
        "/openapi/video/v2/create",
        payload=_duix_cloud_build_video_payload(scene_id, audio_url, task_id),
    )
    video_data = data.get("data") or {}
    video_id = video_data.get("videoId") or video_data.get("id")
    if not video_id:
        logger.warning("Duix cloud video creation response did not include videoId")
        return ""

    logger.info(f"Duix cloud video task submitted: {video_id}")
    return str(video_id)


def _duix_cloud_wait_for_video(video_id: str) -> str:
    timeout = int(
        config.app.get("duix_cloud_timeout", _DUIX_CLOUD_DEFAULT_TIMEOUT_SECONDS)
        or _DUIX_CLOUD_DEFAULT_TIMEOUT_SECONDS
    )
    poll_interval = max(
        5, int(config.app.get("duix_cloud_poll_interval", 5) or 5)
    )
    deadline = time.time() + timeout

    while time.time() < deadline:
        data = _duix_cloud_request("GET", f"/openapi/video/v2/get/{video_id}")
        task_data = data.get("data") or {}
        status = str(task_data.get("synthesisStatus", "")).strip()

        if status == "3":
            video_url = task_data.get("videoUrl")
            if video_url:
                logger.success("Duix cloud digital human video is ready")
                return str(video_url)
            logger.warning("Duix cloud video task succeeded without videoUrl")
            return ""

        if status in {"4", "6", "7"}:
            logger.warning(f"Duix cloud video task failed: status={status}")
            return ""

        logger.info(f"Duix cloud video task status: {status or 'pending'}")
        time.sleep(poll_interval)

    logger.warning(f"Duix cloud video task timed out after {timeout}s")
    return ""


def _generate_with_duix_cloud(
    task_id: str,
    avatar_file: str,
    audio_file: str,
    script_text: str = "",
) -> str:
    scene_id = _config_str("duix_cloud_default_scene_id")
    if not scene_id:
        training_id = _duix_cloud_submit_training(task_id, avatar_file)
        if not training_id:
            return ""
        scene_id = _duix_cloud_wait_for_training(training_id)

    if not scene_id:
        return ""

    video_id = _duix_cloud_create_audio_video(
        task_id=task_id,
        scene_id=scene_id,
        audio_file=audio_file,
    )
    if not video_id:
        return ""

    video_url = _duix_cloud_wait_for_video(video_id)
    if not video_url:
        return ""

    output_file = os.path.join(utils.task_dir(task_id), "digital-human.mp4")
    if not _download_result(video_url, output_file):
        return ""
    return output_file


def _kling_base_url() -> str:
    return _config_str("kling_base_url", _KLING_DEFAULT_BASE_URL).rstrip("/")


def _kling_access_key() -> str:
    return _config_str("kling_access_key")


def _kling_secret_key() -> str:
    return _config_str("kling_secret_key")


def _kling_api_key() -> str:
    # Some compatible gateways expose a plain bearer token instead of AK/SK JWT.
    return _config_str("kling_api_key")


def _kling_request_timeout() -> int:
    return max(5, int(config.app.get("kling_request_timeout", 30) or 30))


def _kling_endpoint(path: str) -> str:
    return f"{_kling_base_url()}/{path.lstrip('/')}"


def _kling_headers() -> dict:
    api_key = _kling_api_key()
    if api_key:
        return {"Authorization": f"Bearer {api_key}"}

    access_key = _kling_access_key()
    secret_key = _kling_secret_key()
    if not access_key or not secret_key:
        logger.warning("Kling access key or secret key is not configured")
        return {}

    now = int(time.time())
    token = jwt.encode(
        {
            "iss": access_key,
            "exp": now + int(config.app.get("kling_jwt_ttl", 1800) or 1800),
            "nbf": now - int(config.app.get("kling_jwt_nbf_skew", 5) or 5),
        },
        secret_key,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def _kling_success(data: dict) -> bool:
    if not isinstance(data, dict):
        return False
    code = data.get("code")
    if code is None:
        return "data" in data
    return str(code).strip() in {"0", "200"}


def _kling_request(
    method: str,
    path: str,
    payload: dict | None = None,
    timeout: int | None = None,
) -> dict:
    headers = _kling_headers()
    if not headers:
        return {}
    headers["Content-Type"] = "application/json"

    try:
        response = requests.request(
            method=method,
            url=_kling_endpoint(path),
            json=payload,
            headers=headers,
            timeout=timeout or _kling_request_timeout(),
            verify=config.app.get("tls_verify", True),
        )
    except Exception as exc:
        logger.warning(f"failed to request Kling {path}: {str(exc)}")
        return {}

    if response.status_code >= 400:
        logger.warning(f"Kling {path} failed: {response.status_code}")
        return {}

    data = _safe_json(response)
    if not _kling_success(data):
        logger.warning(
            f"Kling {path} returned an error: "
            f"{data.get('code')} {data.get('message', '')}"
        )
        return {}
    return data


def _kling_public_base_url() -> str:
    return (_config_str("kling_public_base_url") or _config_str("endpoint")).rstrip("/")


def _kling_url_is_allowed(url: str) -> bool:
    if config.app.get("kling_allow_local_urls", False):
        return True
    return _duix_cloud_url_is_allowed(url)


def _kling_file_url(file_path: str, purpose: str) -> str:
    if _looks_like_url(file_path):
        return file_path

    if not file_path or not os.path.exists(file_path):
        logger.warning(f"Kling {purpose} file does not exist")
        return ""

    public_base_url = _kling_public_base_url()
    if not public_base_url:
        logger.warning(
            "Kling needs kling_public_base_url or endpoint to expose "
            f"the {purpose} file as a public URL"
        )
        return ""

    if not _kling_url_is_allowed(public_base_url):
        logger.warning(
            "Kling public base URL must be reachable from the public internet; "
            "localhost or private network URLs are not accepted by default"
        )
        return ""

    tasks_root = os.path.abspath(utils.task_dir())
    resolved_path = os.path.abspath(file_path)
    if not resolved_path.startswith(tasks_root + os.sep):
        logger.warning(f"Kling {purpose} file is not under the task storage dir")
        return ""

    relative_path = os.path.relpath(resolved_path, tasks_root).replace(os.sep, "/")
    return f"{public_base_url.rstrip('/')}/tasks/{quote(relative_path, safe='/')}"


def _kling_lip_sync_path() -> str:
    return _config_str("kling_lip_sync_path", "/v1/videos/lip-sync")


def _kling_query_paths(task_id: str) -> list[str]:
    configured = _config_str("kling_query_path_template")
    paths = []
    if configured:
        paths.append(configured.format(task_id=task_id))

    lip_sync_path = _kling_lip_sync_path().rstrip("/")
    paths.extend(
        [
            f"{lip_sync_path}/{task_id}",
            f"/v1/videos/{task_id}",
        ]
    )

    unique_paths = []
    for path in paths:
        if path and path not in unique_paths:
            unique_paths.append(path)
    return unique_paths


def _kling_build_payload(video_url: str, audio_url: str, task_id: str) -> dict:
    payload_format = _config_str("kling_payload_format", "input").lower()
    model_name = _config_str("kling_model_name")

    if payload_format == "flat":
        payload = {
            "video_url": video_url,
            "audio_url": audio_url,
        }
        if model_name:
            payload["model_name"] = model_name
        return payload

    payload = {
        "input": {
            "video_url": video_url,
            "mode": _config_str("kling_lip_sync_mode", "audio2video"),
            "audio_type": _config_str("kling_audio_type", "url"),
            "audio_url": audio_url,
        }
    }
    if model_name:
        payload["model_name"] = model_name

    callback_url = _config_str("kling_callback_url")
    if callback_url:
        payload["callback_url"] = callback_url

    external_task_id = _config_str("kling_external_task_id_prefix")
    if external_task_id:
        payload["external_task_id"] = f"{external_task_id}-{task_id}"

    return payload


def _kling_extract_task_id(data: dict) -> str:
    task_data = data.get("data") or data
    for key in ("task_id", "taskId", "id"):
        if isinstance(task_data, dict) and task_data.get(key):
            return str(task_data[key])
    return ""


def _kling_extract_video_url(task_data: dict) -> str:
    for key in ("video_url", "videoUrl", "url"):
        if task_data.get(key):
            return str(task_data[key])

    result = task_data.get("task_result") or task_data.get("taskResult") or {}
    if isinstance(result, dict):
        for key in ("video_url", "videoUrl", "url"):
            if result.get(key):
                return str(result[key])
        videos = result.get("videos")
        if isinstance(videos, list):
            for item in videos:
                if isinstance(item, dict):
                    for key in ("url", "video_url", "videoUrl"):
                        if item.get(key):
                            return str(item[key])
    return ""


def _kling_status_value(task_data: dict) -> str:
    for key in ("task_status", "taskStatus", "status"):
        if task_data.get(key) is not None:
            return str(task_data[key]).strip().lower()
    return ""


def _kling_create_lip_sync(task_id: str, avatar_file: str, audio_file: str) -> str:
    if not _is_video_file(avatar_file):
        logger.warning(
            "Kling lip-sync currently requires a spokesperson video; "
            "photo-only material should use another image-to-video route first"
        )
        return ""

    video_url = _kling_file_url(avatar_file, "spokesperson video")
    audio_url = _kling_file_url(audio_file, "audio")
    if not video_url or not audio_url:
        return ""

    data = _kling_request(
        "POST",
        _kling_lip_sync_path(),
        payload=_kling_build_payload(video_url, audio_url, task_id),
    )
    kling_task_id = _kling_extract_task_id(data)
    if not kling_task_id:
        logger.warning("Kling lip-sync response did not include a task id")
        return ""
    logger.info(f"Kling lip-sync task submitted: {kling_task_id}")
    return kling_task_id


def _kling_wait_for_video(task_id: str) -> str:
    timeout = int(
        config.app.get("kling_timeout", _KLING_DEFAULT_TIMEOUT_SECONDS)
        or _KLING_DEFAULT_TIMEOUT_SECONDS
    )
    poll_interval = max(5, int(config.app.get("kling_poll_interval", 5) or 5))
    deadline = time.time() + timeout
    success_values = {"succeed", "succeeded", "success", "completed", "complete", "3"}
    failure_values = {"failed", "fail", "failure", "error", "4", "5", "6", "7"}

    while time.time() < deadline:
        task_data = {}
        for path in _kling_query_paths(task_id):
            data = _kling_request("GET", path)
            task_data = data.get("data") or data
            if task_data:
                break

        status = _kling_status_value(task_data)
        if status in success_values:
            video_url = _kling_extract_video_url(task_data)
            if video_url:
                logger.success("Kling digital human video is ready")
                return video_url
            logger.warning("Kling task succeeded without video URL")
            return ""

        if status in failure_values:
            message = task_data.get("task_status_msg") or task_data.get("message") or ""
            logger.warning(f"Kling lip-sync task failed: status={status}, message={message}")
            return ""

        logger.info(f"Kling lip-sync task status: {status or 'pending'}")
        time.sleep(poll_interval)

    logger.warning(f"Kling lip-sync task timed out after {timeout}s")
    return ""


def _generate_with_kling(
    task_id: str,
    avatar_file: str,
    audio_file: str,
    script_text: str = "",
) -> str:
    kling_task_id = _kling_create_lip_sync(task_id, avatar_file, audio_file)
    if not kling_task_id:
        return ""

    video_url = _kling_wait_for_video(kling_task_id)
    if not video_url:
        return ""

    output_file = os.path.join(utils.task_dir(task_id), "digital-human.mp4")
    if not _download_result(video_url, output_file):
        return ""
    return output_file


def _safe_json(response) -> dict:
    try:
        return response.json()
    except Exception:
        return {}


def _wait_for_duix_result(job_code: str) -> str:
    timeout = int(
        config.app.get("digital_human_timeout", _DIGITAL_HUMAN_TIMEOUT_SECONDS)
        or _DIGITAL_HUMAN_TIMEOUT_SECONDS
    )
    poll_interval = max(2, int(config.app.get("digital_human_poll_interval", 5) or 5))
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            response = requests.get(
                _duix_endpoint(f"query?code={job_code}"),
                timeout=30,
                verify=config.app.get("tls_verify", True),
            )
        except Exception as exc:
            logger.warning(f"failed to poll Duix digital human task: {str(exc)}")
            time.sleep(poll_interval)
            continue

        if response.status_code >= 400:
            logger.warning(f"Duix query failed: {response.status_code}, {response.text}")
            return ""

        data = _safe_json(response)
        if data and data.get("code") not in (None, 10000, "10000"):
            logger.warning(f"Duix query returned an error: {data}")
            return ""

        task_data = data.get("data", data)
        status = str(task_data.get("status", "")).strip()
        if status == "2":
            result_ref = task_data.get("result") or task_data.get("video_url")
            if result_ref:
                logger.success("Duix digital human video is ready")
                return str(result_ref)
            logger.warning(f"Duix task succeeded without result path: {data}")
            return ""
        if status == "3":
            logger.warning(f"Duix digital human task failed: {data}")
            return ""

        logger.info(f"Duix digital human task status: {status or 'pending'}")
        time.sleep(poll_interval)

    logger.warning(f"Duix digital human task timed out after {timeout}s")
    return ""


def _copy_or_download_duix_result(result_ref: str, output_file: str) -> bool:
    if _looks_like_url(result_ref):
        return _download_result(result_ref, output_file)

    result_candidates = []
    if os.path.isabs(result_ref):
        result_candidates.append(result_ref)
    result_candidates.append(os.path.join(_duix_result_dir(), result_ref))
    result_candidates.append(os.path.join(_duix_workspace_dir(), result_ref))

    for source_file in result_candidates:
        if source_file and os.path.exists(source_file):
            shutil.copyfile(source_file, output_file)
            logger.success(f"Duix digital human video saved: {output_file}")
            return True

    logger.warning(f"Duix result file was not found: {result_ref}")
    return False


def _looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"}


def _download_result(result_url: str, output_file: str) -> bool:
    try:
        response = requests.get(
            result_url,
            stream=True,
            timeout=120,
            verify=config.app.get("tls_verify", True),
        )
    except Exception as exc:
        logger.warning(f"failed to download Duix digital human video: {str(exc)}")
        return False

    if response.status_code >= 400:
        logger.warning(
            f"download Duix digital human video failed: {response.status_code}, {response.text}"
        )
        return False

    with open(output_file, "wb") as fp:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                fp.write(chunk)
    logger.success(f"Duix digital human video saved: {output_file}")
    return True
