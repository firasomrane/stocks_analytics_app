FROM python:3.9.15-alpine3.16

ENV PIPELINE_DIR /usr/src/app
RUN mkdir $PIPELINE_DIR
WORKDIR $PIPELINE_DIR
ENV PYTHONPATH ${PIPELINE_DIR}:$PYTHONPATH

RUN apk add --no-cache gcc musl-dev linux-headers
RUN apk add libpq-dev
RUN python -m pip install --upgrade pip==21.3.1
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . ./pipeline

CMD ["python", "./pipeline/load_data.py"]