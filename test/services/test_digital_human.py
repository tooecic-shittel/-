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
