FROM python:3

RUN apt update && apt install build-essential python-dev nginx --yes &&\
    apt-get clean autoclean &&\
    apt-get autoremove --yes &&\
    rm -rf /var/lib/apt/lists/*

COPY docker/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1

ARG UID=1000
RUN useradd -d /user -l -m -Uu ${UID} -r -s /bin/bash user
COPY docker/nginx.conf /etc/nginx/

COPY --chown=${UID}:${UID} . /app

COPY docker/start.sh /start.sh

RUN chmod 600 /app/docker/ssl/client-key.pem

CMD ["bash", "/start.sh"]