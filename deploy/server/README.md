# 爪爪IP短视频工作流服务器部署

这套部署先把产品跑起来，后续再慢慢优化域名、HTTPS、队列和对象存储。生产密钥只放在服务器的 `config.toml`，不要提交到 GitHub，也不要打进 Docker 镜像。

## 服务器要求

- Ubuntu 22.04/24.04 或同类 Linux
- Docker 和 Docker Compose v2
- 至少 2 核 4G 内存，建议 4 核 8G 起步
- 20G 以上磁盘，生成视频会写入 `storage/`

## 第 1 步：拉代码

```bash
mkdir -p /opt/claw
cd /opt/claw
git clone https://github.com/tooecic-shittel/-.git app
cd app
```

后续更新：

```bash
cd /opt/claw/app
git pull
```

## 第 2 步：准备私有配置

```bash
cd /opt/claw/app
cp -n config.example.toml config.toml
mkdir -p storage
chmod 600 config.toml
```

编辑 `config.toml`，至少确认这些项：

```toml
[app]
hide_config = true
show_admin_config = false
admin_token = "换成一个后台口令"

digital_human_provider = "kling"
kling_base_url = "https://api-beijing.klingai.com"
kling_access_key = "填服务器专用 Access Key"
kling_secret_key = "填服务器专用 Secret Key"
kling_avatar_path = "/v1/videos/avatar/image2video"
kling_tts_path = "/v1/audio/tts"
kling_tts_voice_id = "genshin_vindi2"
kling_tts_voice_language = "zh"
default_tts_voice = "kling:genshin_vindi2-温迪男声"

# 有域名后填同一个公网地址，声音克隆需要它来暴露 /tasks/... 样本文件。
# 官方 Avatar 可留空，因为系统会自动转 Base64。
endpoint = "https://你的域名"
kling_public_base_url = "https://你的域名"

[ui]
tts_server = "kling-tts"
voice_name = "kling:genshin_vindi2-温迪男声"
```

没有域名时，可以先只用 `http://服务器IP:8502` 测 WebUI。此时数字人 Avatar 和可灵 TTS 能跑，声音克隆可能因为样本音频没有公网 `/tasks/...` 地址而回落到预置音色。

## 第 3 步：启动

```bash
cd /opt/claw/app
docker compose -f docker-compose.prod.yml up -d --build
```
默认端口：

- WebUI: `http://服务器IP:8502`
- API: `127.0.0.1:8080`，默认只给本机/Nginx 访问

查看状态：

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f webui
docker compose -f docker-compose.prod.yml logs -f api
```

重启：

```bash
docker compose -f docker-compose.prod.yml restart
```

停止：

```bash
docker compose -f docker-compose.prod.yml down
```

## 可选：Nginx 反代域名

把 `deploy/server/nginx-claw.conf.example` 复制到 Nginx 站点配置后，替换域名并申请 HTTPS 证书。反代后：

- `/` 走 Streamlit WebUI
- `/tasks/`、`/stream/`、`/download/` 走本机 API，用于视频下载和可灵声音克隆样本下载

此时在 `config.toml` 里设置：

```toml
[app]
endpoint = "https://你的域名"
kling_public_base_url = "https://你的域名"
```

## 更新发布

```bash
cd /opt/claw/app
git pull
docker compose -f docker-compose.prod.yml up -d --build
```
