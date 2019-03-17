FROM ubuntu:18.10
MAINTAINER ultmaster scottyugochang@gmail.com
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update \
    && apt-get -y install software-properties-common python python-dev python-pip \
                          locales python3-software-properties python3 python3-dev python3-pip \
                          gcc g++ git libtool python-pip cmake openjdk-8-jdk fp-compiler pypy libboost-all-dev wget \
    && snap install pypy3 \
    && locale-gen en_US.UTF-8
ADD . /ejudge
WORKDIR /ejudge
RUN mkdir -p run/sub run/log run/tmp
ENV LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8
RUN git submodule init && cd nsjail && make && cd ..
RUN useradd -r compiler \
    && wget https://raw.githubusercontent.com/MikeMirzayanov/testlib/master/testlib.h -O /usr/local/include/testlib.h \
    && g++ -o run/spj/defaultspj.bin11 lib/defaultspj.cpp -O2 -std=c++11 -lm \
    && pip3 install -r requirements.txt \
    && chmod +x run.sh
EXPOSE 5000

CMD ./run.sh
