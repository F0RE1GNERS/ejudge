# This dockerfile aims to create a aiplay webserver in the easiest way
# VERSION 1
# Author: ultmaster

FROM ejudge/serverbase:v2
MAINTAINER ultmaster scottyugochang@hotmail.com
ENV DEBIAN_FRONTEND noninteractive

# Copy main code
RUN mkdir -p /var/www/ejudge
COPY . /var/www/ejudge/
WORKDIR /var/www/ejudge

# Install judger
RUN useradd -r compiler
COPY judger/java_policy /etc/
RUN cd judger && chmod +x runtest.sh
RUN cd judger && ./runtest.sh; exit 0

# Install checker
RUN cd testlib && ./build.sh

RUN mkdir ~/.pip
RUN cp docker/judge/pip.conf ~/.pip/pip.conf
RUN pip3 install -r requirements.txt
RUN mkdir -p /judge_server /judge_server/round /judge_server/data /judge_server/tmp

HEALTHCHECK --interval=30s --retries=3 CMD python3 healthcheck.py

EXPOSE 4999

RUN chmod +x run.sh
CMD ./run.sh
