FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN pip install --no-cache-dir flask
RUN pip3 install -r requirements.txt --no-cache-dir

EXPOSE 8502

ENTRYPOINT ["streamlit", "run", "gui.py","--server.port=8502", "--server.address=0.0.0.0"]