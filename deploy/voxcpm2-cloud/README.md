# VoxCPM2 云端配音服务

这个目录用于把 VoxCPM2 部署成独立 GPU TTS 服务，然后给“爪爪电商短视频工作流”调用。

## 推荐架构

WebUI 和视频生成继续跑在普通 CPU 机器上，VoxCPM2 单独跑在 GPU 云机器上：

```text
用户浏览器 -> 爪爪 WebUI/API -> VoxCPM2 GPU 服务 /v1/audio/speech -> 返回 mp3/wav
```

这样成本更好控：只有生成配音时才会占用 GPU，WebUI 不需要绑死在 GPU 机器。

## GPU 机器要求

- NVIDIA GPU，建议先用 24GB 显存级别机器测试，例如 RTX 4090、L40S、A10/A100。
- Docker + NVIDIA Container Toolkit。
- 出站网络能访问 Hugging Face，用于首次下载 `openbmb/VoxCPM2` 模型。

## Docker 启动

进入本目录：

```bash
cp example.env .env
docker compose up --build
```

服务启动完成后，本机地址是：

```text
http://127.0.0.1:8000/v1
```

如果在 RunPod、AutoDL、阿里云、腾讯云这类 GPU 云上运行，把平台提供的公网域名或反向代理域名配置成：

```toml
voxcpm2_base_url = "https://你的域名/v1"
voxcpm2_model_name = "voxcpm2"
```

`config-snippet.toml` 里有完整配置片段。

## 手动启动

如果不用 Docker，可以直接在 GPU 环境里安装 vLLM-Omni，然后启动：

```bash
vllm serve openbmb/VoxCPM2 --omni --host 0.0.0.0 --port 8000 --served-model-name voxcpm2
```

VoxCPM2 的语音风格可以通过 `(声音描述)正文` 传入。当前项目已经把“亲和女声、热情主播、成熟男声”等选项转换成这种格式。

## 自测

服务起来后运行：

```bash
python smoke_test.py --base-url http://127.0.0.1:8000/v1 --output test.mp3
```

如果走了自己的鉴权网关：

```bash
python smoke_test.py --base-url https://你的域名/v1 --api-key 你的服务端token --output test.mp3
```

成功时会生成一个 `test.mp3`。

## 接入当前项目

在项目根目录的 `config.toml` 里配置：

```toml
[app]
default_tts_voice = "voice-catalog:warm_female"
voxcpm2_base_url = "https://你的域名/v1"
voxcpm2_api_key = ""
voxcpm2_model_name = "voxcpm2"
voxcpm2_timeout = 120
voxcpm2_send_voice_prompt = true

[ui]
tts_server = "voice-catalog"
voice_name = "voice-catalog:warm_female"
```

如果 `voxcpm2_base_url` 为空，系统会自动回落到后台配置的 Audio Speech，不会让普通用户看到复杂服务商选项。

## 公网安全

裸 vLLM 服务不要直接暴露给公网。生产环境至少做其中一种：

- 平台安全组只允许 WebUI 服务器访问 GPU 服务。
- 用 Cloudflare Tunnel / Access / Zero Trust 保护域名。
- 用 Nginx、Caddy 或 API 网关校验 Bearer Token，再转发到 `127.0.0.1:8000`。

`voxcpm2_api_key` 只负责让本项目请求时带上 `Authorization: Bearer ...`。如果你要校验这个 token，需要在云端网关里实现或启用对应鉴权。

## 官方参考

- vLLM-Omni GPU 安装文档：https://docs.vllm.ai/projects/vllm-omni/en/stable/getting_started/installation/gpu/
- vLLM-Omni VoxCPM2 Text-to-Speech 示例：https://docs.vllm.ai/projects/vllm-omni/en/stable/user_guide/examples/online_serving/text_to_speech/
- VoxCPM 项目：https://github.com/OpenBMB/VoxCPM
