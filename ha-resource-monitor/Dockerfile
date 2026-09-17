FROM python:3.13-alpine
ARG BUILD_VERSION
ARG BUILD_ARCH
LABEL io.hass.version="${BUILD_VERSION}" io.hass.type="addon" io.hass.arch="${BUILD_ARCH}"

WORKDIR /app
COPY server.py /app/server.py
COPY static /app/static

EXPOSE 8099
CMD ["python3", "/app/server.py"]
