import base64
import os
import shutil
from pathlib import Path

from app.config import config
from app.services import digital_human
from app.utils import utils


class _FakeResponse:
    def __init__(self, status_code=200, payload=None, content=b"", text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self._content = content
        self.text = text

    def json(self):
        return self._payload

    def iter_content(self, chunk_size=1024):
        yield self._content


def _restore_config(snapshot):
    config.app.clear()
    config.app.update(snapshot)


def test_disabled_provider_returns_empty():
    snapshot = dict(config.app)
    try:
        config.app["digital_human_provider"] = "none"
        result = digital_human.generate(
            task_id="digital-human-disabled",
            photo_file="missing.jpg",
            audio_file="missing.mp3",
            script_text="测试",
        )
        assert result == ""
    finally:
        _restore_config(snapshot)


def test_duix_workspace_copy_uses_configured_dir(tmp_path):
    snapshot = dict(config.app)
    try:
        workspace_dir = tmp_path / "duix-temp"
        config.app["duix_workspace_dir"] = str(workspace_dir)
        source = tmp_path / "avatar.mp4"
        source.write_bytes(b"video")

        ref = digital_human._copy_to_duix_workspace(
            str(source), "digital-human-duix-copy", "avatar"
        )

        assert ref == "claw-digital-human-duix-copy-avatar.mp4"
        assert Path(workspace_dir, ref).read_bytes() == b"video"
    finally:
        _restore_config(snapshot)


def test_duix_provider_copies_result(monkeypatch, tmp_path):
    snapshot = dict(config.app)
    task_id = "digital-human-duix"
    task_dir = utils.task_dir(task_id)
    workspace_dir = tmp_path / "duix-temp"
    result_file = workspace_dir / "result.mp4"
    calls = {"post": None, "polls": 0}

    def fake_post(url, json, timeout, verify):
        calls["post"] = {
            "url": url,
            "json": json,
            "timeout": timeout,
            "verify": verify,
        }
        return _FakeResponse(payload={"code": 10000})

    def fake_get(url, timeout=None, verify=None):
        calls["polls"] += 1
        return _FakeResponse(
            payload={"code": 10000, "data": {"status": 2, "result": "result.mp4"}}
        )

    try:
        config.app.update(
            {
                "digital_human_provider": "duix",
                "duix_video_base_url": "http://duix.test:8383",
                "duix_workspace_dir": str(workspace_dir),
                "duix_result_dir": str(workspace_dir),
                "digital_human_timeout": 10,
                "digital_human_poll_interval": 2,
                "tls_verify": False,
            }
        )
        workspace_dir.mkdir(parents=True)
        result_file.write_bytes(b"mp4")
        photo = tmp_path / "avatar.mp4"
        audio = tmp_path / "audio.mp3"
        photo.write_bytes(b"avatar")
        audio.write_bytes(b"audio")

        monkeypatch.setattr(digital_human.requests, "post", fake_post)
        monkeypatch.setattr(digital_human.requests, "get", fake_get)

        result = digital_human.generate(
            task_id=task_id,
            photo_file=str(photo),
            audio_file=str(audio),
            script_text="欢迎来我们店吃牛肉火锅",
        )

        assert result == os.path.join(task_dir, "digital-human.mp4")
        assert Path(result).read_bytes() == b"mp4"
        assert calls["post"]["url"] == "http://duix.test:8383/easy/submit"
        assert calls["post"]["json"]["audio_url"] == "claw-digital-human-duix-audio.mp3"
        assert calls["post"]["json"]["video_url"] == "claw-digital-human-duix-avatar.mp4"
        assert calls["post"]["json"]["code"] == "claw-digital-human-duix"
        assert calls["polls"] == 1
    finally:
        _restore_config(snapshot)
        shutil.rmtree(task_dir, ignore_errors=True)


def test_kling_provider_uses_jwt_headers(monkeypatch):
    snapshot = dict(config.app)
    try:
        config.app.update(
            {
                "digital_human_provider": "kling",
                "kling_access_key": "test-access-key",
                "kling_secret_key": "test-secret-key-with-at-least-32-bytes",
                "kling_api_key": "",
                "kling_jwt_ttl": 1800,
                "kling_jwt_nbf_skew": 5,
            }
        )
        monkeypatch.setattr(digital_human.time, "time", lambda: 1000)

        headers = digital_human._kling_headers()

        assert headers["Authorization"].startswith("Bearer ")
        token = headers["Authorization"].removeprefix("Bearer ")
        token_headers = digital_human.jwt.get_unverified_header(token)
        assert token_headers["typ"] == "JWT"
        decoded = digital_human.jwt.decode(
            token,
            "test-secret-key-with-at-least-32-bytes",
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_nbf": False},
        )
        assert decoded["iss"] == "test-access-key"
        assert decoded["exp"] == 2800
        assert decoded["nbf"] == 995
    finally:
        _restore_config(snapshot)


def test_kling_extracts_video_url_from_task_result():
    task_data = {
        "data": {
            "task_status": "succeed",
            "task_result": {
                "videos": [
                    {
                        "url": "https://cdn.example.test/kling-output.mp4",
                    }
                ]
            },
        }
    }

    assert (
        digital_human._kling_extract_video_url(task_data)
        == "https://cdn.example.test/kling-output.mp4"
    )


def test_kling_avatar_payload_uses_official_fields():
    snapshot = dict(config.app)
    try:
        config.app.update(
            {
                "kling_payload_format": "avatar",
                "kling_avatar_mode": "std",
                "kling_prompt": "",
                "kling_audio_id": "",
            }
        )

        payload = digital_human._kling_build_payload(
            "https://cdn.example.test/avatar.jpg",
            "https://cdn.example.test/audio.mp3",
            "digital-human-kling",
            "欢迎来店里看看今天的新品",
        )

        assert payload == {
            "image": "https://cdn.example.test/avatar.jpg",
            "sound_file": "https://cdn.example.test/audio.mp3",
            "prompt": "欢迎来店里看看今天的新品",
            "mode": "std",
        }
    finally:
        _restore_config(snapshot)


def test_kling_avatar_path_defaults_to_official_endpoint():
    snapshot = dict(config.app)
    try:
        config.app.pop("kling_avatar_path", None)
        config.app["kling_lip_sync_path"] = "/v1/videos/lip-sync"

        assert (
            digital_human._kling_avatar_path()
            == "/v1/videos/avatar/image2video"
        )
    finally:
        _restore_config(snapshot)


def test_kling_avatar_uses_base64_when_public_url_is_not_configured(
    monkeypatch,
    tmp_path,
):
    snapshot = dict(config.app)
    calls = {}

    def fake_request(method, path, payload=None, timeout=None):
        calls["method"] = method
        calls["path"] = path
        calls["payload"] = payload
        return {"code": 0, "data": {"task_id": "kling-task-1"}}

    try:
        config.app.update(
            {
                "kling_payload_format": "avatar",
                "kling_avatar_path": "/v1/videos/avatar/image2video",
                "kling_public_base_url": "",
                "endpoint": "",
                "kling_avatar_mode": "std",
                "kling_prompt": "",
                "kling_audio_id": "",
            }
        )
        avatar = tmp_path / "avatar.jpg"
        audio = tmp_path / "audio.mp3"
        avatar.write_bytes(b"avatar-image")
        audio.write_bytes(b"avatar-audio")
        monkeypatch.setattr(digital_human, "_kling_request", fake_request)

        result = digital_human._kling_create_lip_sync(
            "digital-human-kling-base64",
            str(avatar),
            str(audio),
            "欢迎来店里看看今天的新品",
        )

        assert result == "kling-task-1"
        assert calls["method"] == "POST"
        assert calls["path"] == "/v1/videos/avatar/image2video"
        assert calls["payload"]["image"] == base64.b64encode(b"avatar-image").decode()
        assert calls["payload"]["sound_file"] == base64.b64encode(b"avatar-audio").decode()
    finally:
        _restore_config(snapshot)
