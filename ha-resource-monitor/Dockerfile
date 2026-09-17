FROM python:3.13-alpine

WORKDIR /app
COPY server.py /app/server.py
COPY static /app/static

EXPOSE 8099
CMD ["python3", "/app/server.py"]

