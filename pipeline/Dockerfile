FROM python:3.9.4

ENV PIPELINE_DIR /usr/src/app

# https://stackoverflow.com/a/57764857/7275926
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-dev \
    gcc \
    gfortran \
    musl-dev \
    libpq-dev

RUN mkdir $PIPELINE_DIR
WORKDIR $PIPELINE_DIR
ENV PYTHONPATH ${PIPELINE_DIR}:$PYTHONPATH

RUN python -m pip install --upgrade pip==20.2 setuptools==57.5.0

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . ./pipeline

CMD ["python", "./pipeline/core/load_data.py"]
