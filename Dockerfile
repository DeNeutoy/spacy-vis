FROM python:3.6.3-jessie

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

WORKDIR /stage

# Install base packages.
RUN apt-get update --fix-missing && apt-get install -y \
    bzip2 \
    ca-certificates \
    curl \
    gcc \
    git \
    libc-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    wget \
    libevent-dev \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install npm
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash - && apt-get install -y nodejs

# Copy select files needed for installing requirements.
COPY displacy/ displacy/
RUN pip install -r displacy/requirements.txt

# Build demo
COPY demo/ demo/
RUN cd demo && npm install && npm run build && cd ..
COPY bin/ bin/

# Demo port
EXPOSE 8080


CMD ["/bin/bash"]
