FROM python:3.12-slim

WORKDIR /app
COPY dist/myproject-0.1.0-py3-none-any.whl /tmp/myproject-0.1.0-py3-none-any.whl
RUN python -m pip install --no-cache-dir /tmp/myproject-0.1.0-py3-none-any.whl
COPY configs/baseline.yaml /app/configs/baseline.yaml
RUN chmod 0644 /app/configs/baseline.yaml

ENTRYPOINT ["myproject"]