ARG BASE_IMAGE=ubuntu20.04:custom
FROM ${BASE_IMAGE}
ARG DEBIAN_FRONTEND=noninteractive
RUN dpkg --add-architecture i386 \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
    ca-certificates git gawk qpdf flex bison xxd make gcc g++ \
    libc6:i386 libstdc++6:i386 libncurses5:i386 \
    libgmp-dev libglib2.0-dev libfl-dev zlib1g-dev pkg-config \
    gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu \
    libpcap-dev python3 python2 \
 && rm -rf /var/lib/apt/lists/* \
 && ln -s /usr/bin/python2 /usr/local/bin/python
WORKDIR /work
CMD ["bash"]
