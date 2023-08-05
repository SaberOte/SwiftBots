FROM python:3.11.4-alpine3.18

WORKDIR /app
ENV ENVIRONMENT container

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "main.py"]
