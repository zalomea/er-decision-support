FROM ubuntu:22.04@sha256:5ec03bb3441e8b0bf3b4f9cd4629a1ae763010dc3035bb8da3ae6cf026486401

ARG LLAMA_CPP_REVISION=16d2e01131a07355b1e16086d9d4b76cd35fbb7c

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    cmake \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN git init /llama.cpp && \
    cd /llama.cpp && \
    git remote add origin https://github.com/ggml-org/llama.cpp.git && \
    git fetch --depth=1 origin refs/pull/29831/head && \
    test "$(git rev-parse FETCH_HEAD)" = "${LLAMA_CPP_REVISION}" && \
    git checkout --detach FETCH_HEAD

WORKDIR /llama.cpp

RUN cmake -B build \
    -DCMAKE_BUILD_TYPE=Release \
    -DGGML_CUDA=OFF \
    -DGGML_METAL=OFF \
    -DGGML_VULKAN=OFF && \
    cmake --build build -j --target llama-server

WORKDIR /app

COPY requirements.lock /app/requirements.lock
RUN pip3 install --no-cache-dir -r /app/requirements.lock

COPY download-model.sh /app/download-model.sh
RUN chmod +x /app/download-model.sh

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 5080

CMD ["/app/entrypoint.sh"]
