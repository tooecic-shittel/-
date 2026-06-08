#!/usr/bin/env python3
import argparse
import base64
import json
import pathlib
import sys
import urllib.error
import urllib.request


def normalize_base_url(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    if base_url.endswith("/v1"):
        return base_url
    return f"{base_url}/v1"


def audio_to_data_url(audio_path: str) -> str:
    path = pathlib.Path(audio_path).expanduser().resolve()
    suffix = path.suffix.lower().lstrip(".") or "wav"
    mime = "mpeg" if suffix == "mp3" else suffix
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:audio/{mime};base64,{encoded}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Test a VoxCPM2 /v1/audio/speech service.")
    parser.add_argument("--base-url", required=True, help="Service base URL, e.g. https://host/v1 or http://host:8000/v1")
    parser.add_argument("--api-key", default="", help="Optional bearer token used by your gateway")
    parser.add_argument("--model", default="voxcpm2")
    parser.add_argument("--voice", default="default")
    parser.add_argument("--output", default="voxcpm2-smoke.mp3")
    parser.add_argument("--instruction", default="年轻女性，亲切自然，像真实店主介绍产品，普通话。")
    parser.add_argument("--text", default="大家好，欢迎来到爪爪电商短视频工作流。今天这条声音来自 VoxCPM2 云端服务。")
    parser.add_argument("--ref-audio", default="", help="Optional local reference audio for voice cloning")
    args = parser.parse_args()

    request_text = f"({args.instruction.strip()}){args.text.strip()}" if args.instruction else args.text.strip()
    payload = {
        "model": args.model,
        "voice": args.voice,
        "input": request_text,
        "response_format": "mp3",
    }
    if args.ref_audio:
        payload["ref_audio"] = audio_to_data_url(args.ref_audio)

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if args.api_key:
        headers["Authorization"] = f"Bearer {args.api_key}"

    endpoint = f"{normalize_base_url(args.base_url)}/audio/speech"
    request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        print(exc.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1

    if len(data) < 1000:
        print(f"Audio response is too small: {len(data)} bytes", file=sys.stderr)
        return 1

    output_path = pathlib.Path(args.output).expanduser().resolve()
    output_path.write_bytes(data)
    print(f"OK: saved {len(data)} bytes to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
