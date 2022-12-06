FROM python:3.9.15-alpine3.16

ENV PIPELINE_DIR /usr/src/app

RUN python -m pip install --upgrade pip==20.2 setuptools==57.5.0

RUN apk add --no-cache --update \
    python3 python3-dev gcc \
    gfortran musl-dev

RUN mkdir $PIPELINE_DIR
WORKDIR $PIPELINE_DIR
ENV PYTHONPATH ${PIPELINE_DIR}:$PYTHONPATH

RUN apk add --no-cache gcc musl-dev linux-headers
RUN apk add libpq-dev
RUN python -m pip install --upgrade pip==21.3.1
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . ./pipeline

CMD ["python", "./pipeline/core/load_data.py"]
