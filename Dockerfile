FROM        centos:latest

LABEL       Name="prkeeper" \
            Author="Brad Frank" \
            Maintainer="bradley.frank@gmail.com" \
            Description="Container for downloading and indexing public records appeals."

RUN         yum -y install epel-release && \
            yum -y install python36 python36-pip libreoffice-core

WORKDIR     /opt/prkeeper
COPY        . ./
RUN         chmod 755 main.py

RUN         pip3 install -r /opt/prkeeper/requirements.txt

ENTRYPOINT  ["/opt/prkeeper/main.py"]
CMD         ["--resume"]
