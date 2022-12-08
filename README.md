

# How to use the app

After installing prerequisites
## Steps
- 1 Create external volume to store our data
```
docker volume create db-volume
```
## How to populate data to a DB table
```
make run_pipeline
```


## Use the API:

- with Curl
```
curl -X 'GET' \
  'http://0.0.0.0:8000/stock_metrics/?ticker=AAPL&start=2010-10-10&end=2010-12-10&price_column=open_price&metric=median&rolling_window=10' \
  -H 'accept: application/json'
```

- Using the url:
http://0.0.0.0:8000/stock_metrics/?ticker=AAPL&start=2010-10-10&end=2010-12-10&price_column=open_price&metric=median&rolling_window=10


### Input validation
For the validation I relied mostly on FastAPI already built in tools for easier HTTP exceptions handling.

Use the FastAPI's `Query` to validate the api endpoint query parameters, which when doesn't correspond will automatically raise a [`Unprocessable Entity`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/422) exception with `422` status code.



## Next steps:
- Add test coverage for the API and better input validation with more detailed error messages.
- Add Continuous integration (CI) with Github actions to run all tests.
