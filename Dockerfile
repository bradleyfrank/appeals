FROM        centos:latest

LABEL       Name="prkeeper" \
            Author="Brad Frank" \
            Maintainer="bradley.frank@gmail.com" \
            Description="Container for downloading public records appeals."

RUN         yum -y install epel-release && \
            yum -y install python34 python34-pip

RUN         mkdir /opt/prkeeper /srv/public_records
COPY        . /opt/prkeeper/
RUN         chmod 755 /opt/prkeeper/prkeeper.py

RUN         pip3 install -r /opt/prkeeper/requirements.txt

ENTRYPOINT  ["/opt/prkeeper/prkeeper.py"]
CMD         ["--resume"]