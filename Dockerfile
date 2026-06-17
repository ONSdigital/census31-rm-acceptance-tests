FROM python:3.12.12-slim@sha256:dc9e92fcdc085ad86dda976f4cfc58856dba33a438a16db37ff00151b285c8ca

# install google chrome, chromedriver and add acceptancetest user
RUN apt-get -y update && apt-get install -y curl git wget gnupg jq unzip &&  \
    wget -O /tmp/chrome-versions.json https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json && \
    wget -O /tmp/chrome.zip `jq -r '.channels.Stable.downloads.chrome|.[]|select(.platform=="linux64").url' /tmp/chrome-versions.json` && \
    wget -O /tmp/chromedriver.zip `jq -r '.channels.Stable.downloads.chromedriver|.[]|select(.platform=="linux64").url' /tmp/chrome-versions.json` && \
    # Setup chrome
    unzip /tmp/chrome.zip -d /opt/chrome && \
    ln -s /opt/chrome/chrome-linux64/chrome /usr/local/bin/google-chrome && \
    # Install dependencies for chrome
    while read pkg; do \
      apt-get satisfy -y --no-install-recommends "${pkg}"; \
    done < /opt/chrome/chrome-linux64/deb.deps && \
    # Setup chromedriver
    unzip /tmp/chromedriver.zip chromedriver-linux64/chromedriver -d /usr/local/bin/ && \
    mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    apt-get install -yqq && groupadd --gid 1000 acceptancetests && useradd --create-home --system --uid 1000 --gid acceptancetests acceptancetests

# Install pipenv
RUN pip3 install pipenv

# set display port to avoid crash
ENV DISPLAY=:99
WORKDIR /home/acceptancetests

COPY Pipfile* /home/acceptancetests/
RUN pipenv install --system --deploy --dev
USER acceptancetests

RUN mkdir /home/acceptancetests/.postgresql

COPY --chown=acceptancetests . /home/acceptancetests