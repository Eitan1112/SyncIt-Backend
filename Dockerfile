FROM ubuntu:18.04

RUN apt-get clean && apt-get update -y && \
    apt-get install -y software-properties-common && \ 
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y nginx python3.8 python3-pip python3.8-dev build-essential libssl-dev libffi-dev python3-setuptools swig libasound2-dev libpulse-dev ffmpeg

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN mkdir logs && \ 
    pip3 install -r requirements.txt

COPY . /app

COPY nginx.conf /etc/nginx
RUN chmod +x ./start.sh

RUN touch /app/debug.log && chmod 777 /app/debug.log

CMD [ "./start.sh" ]