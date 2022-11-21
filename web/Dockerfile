FROM ubuntu:22.04

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y software-properties-common gcc && \
    add-apt-repository -y ppa:deadsnakes/ppa

RUN apt update && apt install tzdata -y
ENV TZ="America/Bogota"

RUN apt-get update && apt-get install -y python3.10 python3-distutils python3-pip python3-apt

RUN apt-get update && apt-get install -y \
    ffmpeg

RUN pip install --upgrade pip

# create the appropriate directories
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000