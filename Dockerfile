FROM ubuntu:18.04

RUN apt-get update && apt-get install -y software-properties-common gcc && \
    add-apt-repository -y ppa:deadsnakes/ppa

RUN apt-get update && apt-get install -y python3.10 python3-distutils python3-pip python3-apt

RUN apt-get update && apt-get install -y \
    ffmpeg\
    python-pip

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN echo 'termino' ffmpeg -version
EXPOSE 5000
