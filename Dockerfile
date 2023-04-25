FROM python:3.11

ENV PIP_NO_CACHE_DIR=true
WORKDIR /tmp
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r requirements.txt

WORKDIR /app
COPY . /app
ENTRYPOINT ["python", "src/main.py"]
