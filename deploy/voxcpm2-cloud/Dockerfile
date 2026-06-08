ARG VLLM_OMNI_IMAGE=vllm/vllm-omni:v0.18.0
FROM ${VLLM_OMNI_IMAGE}

ENV HF_HOME=/root/.cache/huggingface
ENV VLLM_LOGGING_LEVEL=INFO

EXPOSE 8000

ENTRYPOINT ["vllm", "serve", "openbmb/VoxCPM2", "--omni", "--host", "0.0.0.0", "--port", "8000", "--served-model-name", "voxcpm2"]
