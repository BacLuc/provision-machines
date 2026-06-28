# renovate: datasource=docker depName=python
FROM python:3.13-slim
WORKDIR /app
COPY server.py .
EXPOSE 11435
CMD ["python", "server.py"]
