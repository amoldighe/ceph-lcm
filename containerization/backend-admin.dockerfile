# vi: set ft=dockerfile :
# Copyright (c) 2016 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


FROM decapod/base
MAINTAINER Mirantis Inc.


LABEL version="0.2.0" description="Admin utilities for Decapod" vendor="Mirantis"
ARG pip_index_url=
ARG npm_registry_url=
ENV DECAPOD_URL=http://frontend:80 DECAPOD_LOGIN=root DECAPOD_PASSWORD=root EDITOR=vim


COPY .git /project/.git


RUN set -x \
  && apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927 \
  && echo "deb http://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.2 multiverse" > /etc/apt/sources.list.d/mongodb.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
    cron \
    curl \
    gcc \
    git \
    less \
    libffi-dev \
    libpython2.7 \
    libssl-dev \
    mongodb-org-tools \
    nano \
    openssh-client \
    python2.7 \
    python3-apt \
    python3-dev \
    python3-pip \
    python-dev \
    python-pip \
    python-setuptools \
    vim \
  && cd /project \
  && git reset --hard \
  && git submodule update --init --recursive \
  && echo "cron=$(git rev-parse HEAD)" >> /etc/git-release \
  && echo "cron=$(scd -s git_pep440 -p)" >> /etc/decapod-release \
  && scd -s git_pep440 -v \
  && pip2 install --no-cache-dir --disable-pip-version-check --upgrade 'setuptools==32.3.1' \
  && pip2 install --no-cache-dir --disable-pip-version-check \
    ./backend/ansible \
    ./backend/monitoring \
  && pip3 install --no-cache-dir --disable-pip-version-check \
    ./decapodlib \
    ./decapodcli \
    ./backend/api \
    ./backend/controller \
    ./backend/admin \
  && _DECAPOD_ADMIN_COMPLETE=source decapod-admin >> /root/.bashrc || true \
  && _DECAPOD_COMPLETE=source decapod >> /root/.bashrc || true \
  && ln -s /usr/local/bin/decapod /usr/bin/cli \
  && ln -s /usr/local/bin/decapod-admin /usr/bin/admin \
  && curl --silent --show-error --fail --location \
    --header "Accept: application/tar+gzip, application/x-gzip, application/octet-stream" -o - \
    "https://caddyserver.com/download/build?os=linux&arch=amd64&features=" | \
    tar --no-same-owner -C /usr/bin/ -xz caddy \
  && chmod 0755 /usr/bin/caddy \
  && mkdir -p /www \
  && cat containerization/files/crontab | crontab - \
  && mkdir -p /etc/caddy \
  && mv containerization/files/cron-caddyfile /etc/caddy/config \
  && mkfifo /var/log/cron.log \
  && cd / \
  && rm -r /project \
  && apt-key del EA312927 \
  && rm /etc/apt/sources.list.d/mongodb.list \
  && apt-get clean \
  && apt-get purge -y \
    gcc \
    git \
    libffi-dev \
    libssl-dev \
    python3-dev \
    python3-pip \
    python-dev \
    python-pip \
  && apt-get autoremove --purge -y \
  && rm -r /var/lib/apt/lists/*


EXPOSE 8000


ENTRYPOINT ["/usr/bin/dumb-init", "-c", "--"]
CMD ["dockerize", "-wait", "tcp://database:27017", "--", "sh", "-c", "caddy -conf /etc/caddy/config & cron & tail -F /var/log/cron.log"]