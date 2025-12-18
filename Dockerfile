# syntax=docker/dockerfile:1

FROM ghcr.io/linuxserver/unrar:latest AS unrar

FROM ghcr.io/linuxserver/baseimage-alpine:3.22

# set version label
ARG BUILD_DATE
ARG VERSION
ARG BAZARR_VERSION="1.0.3-cappy"
LABEL build_version="Linuxserver.io version:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="korewaChino"
# hard set UTC in case the user does not define it
ENV TZ="Etc/UTC"

RUN \
  echo "**** install build packages ****" && \
  apk add --no-cache --virtual=build-dependencies \
    build-base \
    cargo \
    libffi-dev \
    libpq-dev \
    libxml2-dev \
    libxslt-dev \
    nodejs \
    npm \
    python3-dev && \
  echo "**** install packages ****" && \
  apk add --no-cache \
    ffmpeg \
    libxml2 \
    libxslt \
    mediainfo \
    python3
RUN \
  echo "**** install bazarr ****" && \
  mkdir -p /app/bazarr/bin

# Copy source code to temporary location
COPY . /src

# Build frontend
RUN \
  echo "**** building frontend ****" && \
  cd /src/frontend && \
  npm install && \
  npm ci && \
  npm run build && \
  echo "**** frontend build complete ****"

# Set up Bazarr
RUN \
  echo "**** copying bazarr files ****" && \
  cp -r /src/bazarr /app/bazarr/bin/ && \
  cp -r /src/libs /app/bazarr/bin/ && \
  cp -r /src/custom_libs /app/bazarr/bin/ && \
  cp -r /src/migrations /app/bazarr/bin/ && \
  cp -r /src/frontend /app/bazarr/bin/ && \
  cp /src/bazarr.py /app/bazarr/bin/ && \
  cp /src/requirements.txt /app/bazarr/bin/ && \
  cp /src/postgres-requirements.txt /app/bazarr/bin/ && \
  echo "**** create VERSION file ****" && \
  if [ -n "${BAZARR_VERSION}" ]; then \
    echo "${BAZARR_VERSION}" > /app/bazarr/bin/bazarr/VERSION; \
  else \
    echo "v0.0.0-dev" > /app/bazarr/bin/bazarr/VERSION; \
  fi && \
  echo "UpdateMethod=docker\nBranch=master\nPackageVersion=${VERSION}\nPackageAuthor=linuxserver.io" > /app/bazarr/package_info && \
  echo "**** Install requirements ****" && \
  python3 -m venv /lsiopy && \
  /lsiopy/bin/pip install -U --no-cache-dir \
    pip \
    wheel && \
  /lsiopy/bin/pip install -U --no-cache-dir --find-links https://wheel-index.linuxserver.io/alpine-3.22/ \
    -r /app/bazarr/bin/requirements.txt \
    -r /app/bazarr/bin/postgres-requirements.txt && \
  printf "Linuxserver.io version: ${VERSION}\nBuild-date: ${BUILD_DATE}" > /build_version && \
  echo "**** clean up ****" && \
  apk del --purge \
    build-dependencies && \
  rm -rf \
    $HOME/.cache \
    $HOME/.cargo \
    /tmp/* \
    /src

# add local files
COPY root/ /

# add unrar
COPY --from=unrar /usr/bin/unrar-alpine /usr/bin/unrar

# ports and volumes
EXPOSE 6767

VOLUME /config
