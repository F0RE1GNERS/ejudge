FROM ubuntu:16.04
MAINTAINER ultmaster scottyugochang@hotmail.com
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update \
    && apt-get -y install software-properties-common python-software-properties python python-dev python-pip \
                          locales python3-software-properties python3 python3-dev python3-pip \
                          gcc g++ git libtool python-pip libseccomp-dev cmake openjdk-8-jdk nginx redis-server \
                          mono-devel php gfortran perl ghc scala nodejs nodejs-legacy \
                          rustc fp-compiler clang pypy mono-complete ocaml-nox \
    && locale-gen en_US.UTF-8 \
    && mkdir -p /ejudge
COPY . /ejudge
WORKDIR /ejudge
ENV LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8
RUN useradd -r compiler \
    && cp sandbox/java_policy /etc/ \
    && mkdir -p run/data run/sub run/log \
    && pip3 install -r requirements.txt \
    && python3 setup.py build_ext --inplace \
    && chmod 600 config/* \
    && chmod +x run.sh \
    && cd tests \
    && python3 test_submission.py \
    && python3 test_runner.py \
    && rm -rf /ejudge/run \
    && mkdir -p run/data run/sub run/log
VOLUME /ejudge
EXPOSE 5000

HEALTHCHECK --interval=30s --retries=3 CMD curl http://localhost:5000/ping
CMD ./run.sh
