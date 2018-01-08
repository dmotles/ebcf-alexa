FROM python:3.6.4

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install zip -y

WORKDIR /build
COPY requirements.txt requirements.txt
COPY infra-requirements.txt infra-requirements.txt

# Install requirements for running tests
RUN pip3 install -r infra-requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install awscli
