FROM python:3.6.4

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install zip -y

RUN pip3 install awscli pytest boto3

RUN pip3 install pytz

RUN echo "Built - nothing special"
