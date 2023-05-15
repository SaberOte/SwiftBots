FROM python:3.11.3-alpine3.18

ARG entity
ENV ENTITY $entity
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "main.py", "start", "-d"]
