# Duix Avatar 云 GPU 部署指南

这套部署方式面向“爪爪电商短视频工作流 + Duix Avatar 自建数字人”的同机部署。

目标架构：

```text
同一台云 GPU 服务器
├── 爪爪 WebUI              8502 对外测试，8501 容器默认端口
├── 爪爪 API                8080 默认只监听本机
├── Duix Avatar 视频服务     8383
├── Duix Avatar 语音服务     18180
├── Duix ASR 服务           10095
└── 共享目录                /opt/duix_avatar_data/face2face/temp
```

## 选服务器

建议先按这个规格租一台测试：

- Ubuntu 22.04
- NVIDIA GPU，优先 RTX 4070/4090 或同等级云卡
- 显存 12GB 起步，越大越稳
- 内存 32GB 起步
- 磁盘 100GB 起步，建议 200GB
- Docker、Docker Compose、NVIDIA Container Toolkit

Duix 官方说明里，本地 Docker 部署需要 NVIDIA GPU 环境，部署过程会拉较大的镜像，首次安装要预留较长时间。

## 目录约定

推荐统一放到 `/opt`：

```bash
sudo mkdir -p /opt/claw
sudo mkdir -p /opt/duix-avatar
sudo mkdir -p /opt/duix_avatar_data/face2face/temp
sudo chown -R "$USER:$USER" /opt/claw /opt/duix-avatar /opt/duix_avatar_data
```

## 第 1 步：准备服务器 GPU 环境

先确认宿主机能看到显卡：

```bash
nvidia-smi
```

确认 Docker 能把 GPU 挂进容器：

```bash
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
```

如果这一步失败，先装 NVIDIA Container Toolkit。官方文档：

```text
https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html
```

## 第 2 步：部署 Duix Avatar

```bash
cd /opt
git clone https://github.com/duixcom/Duix-Avatar.git duix-avatar
cd /opt/duix-avatar

export DUIX_HOME=/opt/duix_avatar_data
docker compose -f docker-compose-linux.yml up -d
```

检查服务：

```bash
docker ps
curl http://127.0.0.1:8383/easy/query?code=health-check
```

`query` 返回任务不存在也没关系，能连通 `8383` 就说明视频服务端口起来了。

## 第 3 步：部署爪爪项目

把本项目放到 `/opt/claw` 后：

```bash
cd /opt/claw
cp config.example.toml config.toml
```

如果你已经有 `config.toml`，不要覆盖它，里面的 LLM、TTS、Pexels、MiniMax key 会继续保留。

把 Duix 配置写进去：

```bash
python deploy/duix-gpu/configure_duix.py \
  --mode docker \
  --duix-home /opt/duix_avatar_data
```

然后启动：

```bash
export DUIX_HOME=/opt/duix_avatar_data
docker compose -f docker-compose.yml -f deploy/duix-gpu/docker-compose.duix.yml up -d --build
```

访问：

```text
http://服务器IP:8502
```

## 第 4 步：后台确认配置

后台模式里应该看到：

```text
数字人口播服务：Duix Avatar
Duix 视频服务地址：http://host.docker.internal:8383
Duix 共享素材目录：/duix_workspace/face2face/temp
```

如果不用 Docker 跑爪爪，而是在宿主机直接跑 Python，则配置改成：

```toml
digital_human_provider = "duix"
duix_video_base_url = "http://127.0.0.1:8383"
duix_workspace_dir = "/opt/duix_avatar_data/face2face/temp"
duix_result_dir = "/opt/duix_avatar_data/face2face/temp"
```

## 第 5 步：测试流程

推荐先用短素材测试：

1. 填一个 10-20 秒左右的电商口播文案。
2. 开启“老板/主播数字人口播”。
3. 上传 5-15 秒正脸视频，先不要用照片。
4. 视频来源先选“上传真实素材”或 Pexels。
5. 生成 1 条视频。

跑通视频版后，再测试上传照片。照片会自动转成一段短视频再送给 Duix，但真实效果通常不如正脸视频稳定。

## 常见问题

### 1. 爪爪提示数字人口播服务未配置

检查 `config.toml`：

```toml
digital_human_provider = "duix"
duix_video_base_url = "http://host.docker.internal:8383"
duix_workspace_dir = "/duix_workspace/face2face/temp"
```

改完后重启爪爪容器：

```bash
docker compose -f docker-compose.yml -f deploy/duix-gpu/docker-compose.duix.yml restart
```

### 2. Duix 任务一直 pending

先看 Duix 日志：

```bash
cd /opt/duix-avatar
docker compose -f docker-compose-linux.yml logs -f
```

再确认 GPU 是否正常：

```bash
nvidia-smi
```

### 3. Duix 找不到音频或视频

这是共享目录没打通。确认爪爪容器里能看到目录：

```bash
docker exec -it moneyprinterturbo-webui ls -lah /duix_workspace/face2face/temp
```

确认宿主机也能看到同一批文件：

```bash
ls -lah /opt/duix_avatar_data/face2face/temp
```

### 4. 公网访问怎么做

生产环境建议只直接暴露：

- `8502` 或 Nginx/Cloudflare 反代后的 WebUI

API 的 `8080` 如果要给外部系统调用，也建议通过 Nginx/Cloudflare 加鉴权后再暴露。

Duix 的 `8383`、`18180`、`10095` 不建议直接暴露到公网，只给本机或内网访问。

## 参考

- Duix Avatar: https://github.com/duixcom/Duix-Avatar
- NVIDIA Container Toolkit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html
