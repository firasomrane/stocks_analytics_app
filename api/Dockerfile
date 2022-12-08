FROM python:3.9

# Ensure that python output is set straight to the terminal without buffering it first
ENV PYTHONUNBUFFERED 1

ENV APP_DIR /usr/src/app

RUN mkdir $APP_DIR
WORKDIR $APP_DIR

# TODO add a user to not run this as a root

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
COPY . $APP_DIR

# uvicorn apis.main:app --host=0.0.0.0
CMD ["uvicorn", "apis.main:app", "--host", "0.0.0.0"]

EXPOSE 8000
