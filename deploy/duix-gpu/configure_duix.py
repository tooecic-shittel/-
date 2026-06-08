#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

import toml


def parse_args():
    parser = argparse.ArgumentParser(
        description="Configure only Duix Avatar digital-human settings in config.toml."
    )
    parser.add_argument(
        "--config",
        default="config.toml",
        help="Path to config.toml. Defaults to ./config.toml.",
    )
    parser.add_argument(
        "--mode",
        choices=["docker", "host"],
        default="docker",
        help="docker: claw runs in Docker; host: claw runs directly on the GPU host.",
    )
    parser.add_argument(
        "--duix-home",
        default="/opt/duix_avatar_data",
        help="Host path used as DUIX_HOME.",
    )
    parser.add_argument(
        "--video-base-url",
        default="",
        help="Override Duix video service URL.",
    )
    parser.add_argument(
        "--workspace-dir",
        default="",
        help="Override workspace path as seen by the claw process/container.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    config_path = Path(args.config)
    if not config_path.exists():
        raise SystemExit(f"config file not found: {config_path}")

    cfg = toml.load(config_path)
    app = cfg.setdefault("app", {})

    duix_home = os.path.abspath(os.path.expanduser(args.duix_home))
    if args.mode == "docker":
        video_base_url = args.video_base_url or "http://host.docker.internal:8383"
        workspace_dir = args.workspace_dir or "/duix_workspace/face2face/temp"
    else:
        video_base_url = args.video_base_url or "http://127.0.0.1:8383"
        workspace_dir = args.workspace_dir or os.path.join(
            duix_home, "face2face", "temp"
        )

    app["digital_human_provider"] = "duix"
    app["duix_video_base_url"] = video_base_url
    app["duix_workspace_dir"] = workspace_dir
    app["duix_result_dir"] = workspace_dir
    app.setdefault("duix_project_name", "claw-ecommerce")
    app.setdefault("duix_chaofen", False)
    app.setdefault("duix_watermark_switch", False)
    app.setdefault("duix_image_video_duration", 5)
    app.setdefault("duix_image_video_fps", 25)
    app.setdefault("digital_human_timeout", 300)
    app.setdefault("digital_human_poll_interval", 5)

    # Remove the old D-ID-only keys so the admin UI is unambiguous.
    app.pop("did_api_key", None)
    app.pop("did_base_url", None)
    app.pop("digital_human_public_base_url", None)

    config_path.write_text(toml.dumps(cfg), encoding="utf-8")
    print(f"updated {config_path}")
    print(f"digital_human_provider = {app['digital_human_provider']}")
    print(f"duix_video_base_url = {app['duix_video_base_url']}")
    print(f"duix_workspace_dir = {app['duix_workspace_dir']}")


if __name__ == "__main__":
    main()
