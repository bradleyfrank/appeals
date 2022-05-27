FROM        docker.io/python:3.10-slim

LABEL       Name="prkeeper" \
            Author="Brad Frank" \
            Maintainer="bradfrank@fastmail.com" \
            Description="Container for running the PRKeeper application."

RUN         apt update \
            && apt-get install -y libreoffice-core \
            && mkdir /opt/app /opt/docs/

COPY        app/ /opt/app/

RUN         chmod 755 /opt/app/main.py \
            && python3 -m pip install -r /opt/app/requirements.txt

ENTRYPOINT  ["/opt/app/main.py"]
CMD         ["--resume"]