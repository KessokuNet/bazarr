# syntax=docker/dockerfile:1

FROM ghcr.io/linuxserver/unrar:latest AS unrar

FROM ghcr.io/linuxserver/baseimage-alpine:3.22

# set version label
ARG BUILD_DATE
ARG VERSION
ARG BAZARR_VERSION
LABEL build_version="Linuxserver.io version:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="korewaChino"
# hard set UTC in case the user does not define it
ENV TZ="Etc/UTC"

COPY . /src

# Install build packages
RUN apk add --no-cache --virtual=build-dependencies \
    build-base \
    cargo \
    libffi-dev \
    libpq-dev \
    libxml2-dev \
    libxslt-dev \
    python3-dev

# Install runtime packages
RUN apk add --no-cache \
    ffmpeg \
    libxml2 \
    libxslt \
    mediainfo \
    python3

# Install Bazarr
RUN mkdir -p /app/bazarr/bin && \
    cp -av /src/bazarr/. /app/bazarr/bin/ && \
    cp /src/bazarr.py /app/bazarr/bin/bazarr.py && \
    rm -Rf /app/bazarr/bin/bin && \
    echo "UpdateMethod=docker\nBranch=master\nPackageVersion=${VERSION}\nPackageAuthor=linuxserver.io" > /app/bazarr/package_info && \
    cp /src/postgres-requirements.txt /app/bazarr/bin/postgres-requirements.txt

# Install Python requirements
RUN python3 -m venv /lsiopy && \
    pip install -U --no-cache-dir pip wheel && \
    pip install -U --no-cache-dir \
        -r /src/requirements.txt \
        -r /src/postgres-requirements.txt

# Finalize build
RUN printf "Linuxserver.io version: ${VERSION}\nBuild-date: ${BUILD_DATE}" > /build_version && \
    apk del --purge build-dependencies && \
    rm -rf \
        $HOME/.cache \
        $HOME/.cargo \
        /tmp/*

# Add local files
COPY root/ /

# Add unrar
COPY --from=unrar /usr/bin/unrar-alpine /usr/bin/unrar

# Ports and volumes
EXPOSE 6767

VOLUME /config
