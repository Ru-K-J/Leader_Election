FROM python:3.12-slim

WORKDIR /app

COPY original_bully_node.py .

ENTRYPOINT ["python3", "original_bully_node.py"]