FROM        centos:latest

LABEL       Name="prkeeper" \
            Author="Brad Frank" \
            Maintainer="bradley.frank@gmail.com" \
            Description="Container for downloading public records appeals."

RUN         yum -y install epel-release && \
            yum -y install python34 python34-pip && \
            pip3 install python-magic configparser

COPY        . /opt/prkeeper/
RUN         chmod 755 /opt/prkeeper/prkeeper.py
RUN         mkdir /srv/public_records

ENTRYPOINT  ["/opt/prkeeper/prkeeper.py"]
CMD         ["--resume"]