FROM ubuntu:22.04

ENV SENSOR_TYPE="mock"
ENV FREQ_READ_DATA=5
ENV URI_DB_SERVER="127.0.0.1:5432"
ENV MIN_RANGE_VALUE=0
ENV MAX_RANGE_VALUE=10

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt install -y software-properties-common

RUN add-apt-repository ppa:deadsnakes/ppa

# Pre-requisites
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install requirements
ADD ./requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

# Copy project files
WORKDIR /home/sensor_reader
COPY ./ ./app/
WORKDIR /home/sensor_reader/app

CMD python3 -m sensor_reader.app --sensor_type $SENSOR_TYPE --freq_read_data $FREQ_READ_DATA --uri_db_server $URI_DB_SERVER --min_range_value $MIN_RANGE_VALUE --max_range_value $MAX_RANGE_VALUE
