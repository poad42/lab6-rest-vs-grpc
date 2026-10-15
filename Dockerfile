# REST and gRPC environment for the lab6 comparison on Ubuntu 26.04
FROM ubuntu:26.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 \
      python3-pip \
      python3-venv \
      iputils-ping \
      curl \
      ca-certificates \
      && rm -rf /var/lib/apt/lists/*

# REST dependencies from pyproject.toml, plus the gRPC runtime and tools.
RUN python3 -m pip install --break-system-packages \
      "flask>=3.1.3" \
      "jsonpickle>=4.1.2" \
      "pillow>=12.3.0" \
      "requests>=2.34.2" \
      grpcio \
      grpcio-tools \
      && rm -rf /root/.cache/pip*

# python -> python3 symlink (the scripts use "#!/usr/bin/env python3")
RUN ln -sf /usr/bin/python3 /usr/bin/python

RUN mkdir -p /lab
WORKDIR /lab

CMD ["/bin/bash"]
