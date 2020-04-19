FROM        centos:8

LABEL       Name="prkeeper" \
            Author="Brad Frank" \
            Maintainer="bradfrank@fastmail.com" \
            Description="Container for running the PRKeeper application."

RUN         yum -y install epel-release && \
            yum -y install python36 python36-pip libreoffice-core

RUN         mkdir /prkeeper /opt/prkeeper/
COPY        app/ /opt/prkeeper/
RUN         chmod 755 /opt/prkeeper/main.py

RUN         python3 -m pip install -r /opt/prkeeper/requirements.txt

ENTRYPOINT  ["/opt/prkeeper/main.py"]
CMD         ["--resume"]