


# How to use the app


After installing prerequisites
## Prerequisites:
- docker: [link](https://docs.docker.com/get-docker/)
- docker-compose [link](https://docs.docker.com/compose/install/)
- make: `brew install make` if you are using macos
## Steps
- Clone the git repository
- Download, unzip the data and place it in `./pipeline/data` direcotory as it is, so that we end up with 2 files: `./pipeline/data/stocks-2011.csv` and `./pipeline/data/stocks-2010.csv`. [First file link](https://syrup-challenge.s3.us-east-2.amazonaws.com/stocks-2010.csv.gz), [Second file link](https://syrup-challenge.s3.us-east-2.amazonaws.com/stocks-2011.csv.gz)
- Create an external volume for the database to persist the data
```
docker volume create db-volume
```
- Populate data to a DB table
```
make run_pipeline
```
This will populate the stock market data to in `stock` table in a postgres database in `stock_market_data` database running locally.

- 3 Run the API:
```
make run_api
```
This will launch a local web app that uses FastAPI and listens on port 8000 locally


## How to query the API and use the app:

- with Curl
```
curl -X 'GET' \
  'http://0.0.0.0:8000/stock_metrics/?ticker=AAPL&start=2010-10-10&end=2010-12-10&price_column=open_price&metric=median&rolling_window=10' \
  -H 'accept: application/json'
```

- Using the url:
http://localhost:8000/stock_metrics/?ticker=GOOG&start=2010-10-10&end=2010-12-10&price_column=open_price&metric=median&rolling_window=10

To try different input values for `ticker`, `start` and `end` dates ... you can change the query parameters values in either the url or with curl.

### API documentation
- You can find the API documentation visiting `http://localhost:8000/docs`

## Technical choices
The purpose of the app is to compute a metric based on a rolling window between a start and an end date.

### Base idea
- The base idea of implementing this in a web app would be to have a have an app that will load the `dataset in memory at startup time in a pandas DataFrame`, and for each call will perform the filtering and the rolling window metric calculation on the dataframe.
- Here the choice of pandas is because of the support of rolling window aggregation calculation out of the box.
- But a dataframe deosn't support indexes for fast queries or at least supports them but with some complexity and not simple to have multi-column index, that's why filtering on date and ticker won't be fast. But of course for our case ~1M this should work without problems.
- Another problem is that if the dataset is bigger it will no more `fit in memory` and we will start having memory errors using pandas which needs to load the entire data in memory (which can be solved by sharding but adds a ton of complexity).

### The chosen implementation
- The choice of a separate database and not an in-memory one or pandas, is to avoid having memory errors and make sure data is persisted to disk.
- The stock price data is a time-series data in nature, prefered to not go with a time-series database to reduce the complexity for the purpose of this work.
- I have decided to not use Postgres query to compute the rolling window metrics since it is simpler with pandas.
- I have chosen to expose an API over a cli tool that does communicate with an API since this application makes sense as an API service more than a cli tool.


## Implementation Discussion

### 1- If you didn’t implement tests, what kind of testing would you like to see for this application
- We have an analytics problem at hand, where we want to make an aggregation on a column, that is better handled by an OLAP database that will be columnar, but an OLAP database generally don't serve data in melliseceonds and needs other layer to become a good choice for fast serving called a cube. For the simplicity and since we don't have big data here, we will use postgres: an OLTP database.
- Here we would like to test the maximum especially for critical parts like the API response.
- I have added tests to most of the API functions and to our FastAPI metrics target endpoint.\
Tests can be run with `make run_api_tests_local` and then `docker exec -it [container_name] pytest -v` <span id='tests'></span>
- The code that populates the data to the database is missing, we should test with a test db that the populator is adding the data and creating the requested indexes.
- We can test the data preprocessing functions to convert the date columns to the ISO format.

### 2- How did you handle and validate user inputs?
- I added custom validation for the input parameters (`ticker`, `date`, ...). They are defined in `api/apis/stock_functions.py` file like `StartDateValidation`.\
I have added tests for these validations.
- I relied also on FastAPI built in parameters validation tools like `Query(default=Required, min_length=1, max_length=5)` for `ticker` parameters.
- For each invalid input a HTTPError with status code 422 is returned with message detailing the problem:\
Example visiting [this link](http://0.0.0.0:8000/stock_metrics/?ticker=AAPL&start=2010-04-01&end=2010-11-01&price_column=any_name&metric=max&rolling_window=11) \
returns a http error with `{"detail":"Price column should be one of ['high_price', 'low_price', 'open_price', 'close_price']"}` as message

### 3- What optimizations did you make to speed up run-time? What additional optimizations would you like to make?

- For each request we need to compute the rolling window metric for each date between start and end date. One optimization is `to not compute the rolling window metric for all the dates` and then filter the requested ones, but instead filter only the needed dates .\
 Since the data is not present for each contiguous date due to holidays or days on which to stock exchange can be close, then calculating starting from **(start_date - rolling_window (days))** won't work and we need to take some more safety to consider the holidays and maybe missing data on some days.

 But doing this data analysis. executing this query
  ```
  with with_dates_lag AS (
    select
      name,
      date,
      lag(date, 1) over(partition by name order by date asc) as lagging_date
    from stock
  ),
  days_diff AS (
    select
      *
      extract(day from date::timestamp - lagging_date::timestamp) as days_diff
    from with_dates_lag
    where lagging_date is not null
  )

  select * from days_diff
  order by days_diff desc;
  ```
  |name |date      |lagging_date|days_diff|
  |-----|----------|------------|---------|
  |FIF  |2011-09-28|2010-02-18  |587      |
  |EMO  |2011-06-10|2010-05-13  |393      |
  |KOS  |2011-05-11|2010-05-24  |352      |
  |FF   |2011-03-23|2010-05-11  |316      |
  |PAR  |2011-01-03|2010-09-24  |101      |
  |NMK-C|2010-12-03|2010-09-16  |78       |
  |NAV-D|2011-06-01|2011-04-06  |56       |
  |MTSL |2010-04-01|2010-02-11  |49       |
  |NAV-D|2010-04-05|2010-02-16  |48       |


  Shows that some stocks may diseapper for longer than `>580` days, which can be due to different reasons, whether the data is not present or that the company went private and then listed again, or it may even be delisted by the stock exchange if it doesn't correspond to the exchange conditions and rules.

  We can do some conditions on only these ~50 outliers but it is not a reliable and scalable way to do things in the long term.
  Due to this, I decided to not use this optimization and to always compute the rolling window metric starting from the first date we have in the dataset which translates to **no filtering on `start_date`**, But **continue to filter on the `end_date`** to avoid wated calculations.\
  We can still filter on `start_date` but will need to have a complex query to be written which involves sorting over `start_date` which is not good for query speed.


- To speed up the run-time when filtering and searching for the target rows based on the ticker and the start and end date, the data was put in a postgres table and added a `b-tree index on (name, date)` to speed up the search.
- I have added postgres table [clustering](https://www.postgresql.org/docs/14/sql-cluster.html) based on the (name, date) index to make the table phisically reordered based on the index information which helps making less random file access in the DB disk and have maximum sequential access to disk which is faster.\
This can be done with such query `CLUSTER stock USING idx_name_date`

- Since the `rolling-window` is small there is no value in <span id="pre-aggregation"> **`pre-aggregating`**</span> the metrics that we can aggregate on top like `MAX` and `MIN`. \
By pre-aggregation here we mean that:
  - we can pre-aggregate `MIN` and `MAX` for each group of 100 subsequent dates,
  - then to find the `MIN` for 910 dates we just need to aggregate on top of 9 of the pre-aggregated metrics + 10 non pre-aggregated metrics.
  - `STD` and `MEAN` also can be pre-aggregated but need additional data to store to be able to aggregate on top. `Median` can't be pre-aggregated.\

  This will introduce complexity and can be beneficial only on big amount of data, for example in the case where we have the stock market data for each minute and for a extended number of years.

- I use sql `COPY` for faster data population to the DB table.

- Another thing to consider is caching. By having another layer where the API will do the look-up before querying the database.

**Remark**:\
Both `pre-aggregation` and `caching` are used by BI tools for faster dashboarding and fast calculation of aggregations. This layer is generally called a cube (eg: [cube.dev](https://cube.dev/)). They can be used with postgres database in our case. But generally they are used with OLAP databases to make serving faster.

### 4- If it had to serve many queries at once — when would it start to break and how
would you scale past that point?
<span id="many_queries"></span>

Using 1 instance serving the API is already `not fault tolerant`, so when the machine that we use is down, the service will be down, => We need more than 1 instance serving the API.\
If we start receiving thousands of requests per second then 1 instance should break and won't be able to handle that amount of concurrent requests. This will depend on the machine config (CPU) used to run the service and on the cpu resources used by each request. Some load-testing is necessary to have a better idea on the numbers.

- If we start having multiple queries at once we need to scale the app horizontalaly and make more instances running the stateless api service and place a load-balancer in front to load-balance between the instances, such thing is easy to declare and deploy with Kubernetes (using load balancer service) and a deployment behind that will `auto-scale` the Replicaset based on the CPU usage of the pods.

- Use dB connection pools to reduce the time taken to create connections to the db and make connections reusable.

- Use async dB calls and async api functions to have concurrency and not wait for dB calls while returned. This should be out of the box in FasApi.

- If we start hitting the max CPU usage of the database instance due to the large number of connections and the required queries overhead then we can scale use `DB replication` and have 1 primary instance for writing and multiple replicas read-only DB instances that we can load-balance the traffic between. \
This introduces some trandoffs between `availability` and `strong consistency of read after write` . These are the different postgres replication modes:
  - Asynchronous Replication => no strong consistency of read after write
  - Synchronous Write Replication
  - Synchronous Apply Replication => Need that all replicas have written => Slower writes


### 5 - If it had to serve queries over larger datasets — when would it start to break and how would you scale past that point?

- If we serve the queries over large datasets then we can hit storage scaling problems where we can `no more scale vertically` our database instance, \
or we can start having slower queries due to the large search space and reduced DB cache compared to the size of the table and the indexes => We need to read from disk more often.

- Stock market data is a `time-series` data and queries are always based on the time. If we had a stock market data with billions of data points, then using a time-series database like will be a better fit since it optimizes for the time-based queries whether on how the data is written to disk and how it is retrieved.\
Databases like TimeScaleDB and InfluxDB can be considered.

- We can use DB `partitioning` which will split the table into smaller phisical pieces and if the partitions are matching the queries (partitioning columns are used for filtering) then the queries search space will decrease and make the queries faster. \
We can paritition based on ticker name and dates, Hash Partitioning on names and Range parititioning on dates. This is supported out of the box for [Postgres](https://www.postgresql.org/docs/14/ddl-partitioning.html). \
This introduces some overhead if we end up with large number of partitions.

- Another option is `Database Sharding`. Stock ticker is a good choice for sharding key, where we can use `hashed sharding` since we can consider that each stock ticker have the same amount of data (with exceptions depending on the date the stock started trading), then distributing them randomly `won't create data skew problems` with some shards being bigger then other ones.\
We can use `Consistent hashing` For a better fault tolerant solution, but generally the database will be hosted in the cloud provider's service where it offers `high availability` and shards can be restored fast if some problems occured.\
Sharding can introduce problems if we have joins between different tables that can't be sharded by the same key, which introduces the complexity of performing multi-shards(distributed) transactions.

### 6 - Additional notes on implementation:
- Here the implementation of the API is very basic and not robust. This to consider are:
  - Rate limiting
  - Circuit breaker
  - Timeouts (for DB queries)
  - Retries and banckoff with DB queries.

### Input validation
For the validation I relied mostly on FastAPI already built in tools for easier HTTP exceptions handling.

Use the FastAPI's `Query` to validate the api endpoint query parameters, which when doesn't correspond will automatically raise a [`Unprocessable Entity`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/422) exception with `422` status code.


## Feature Expansion Discussion: Most Similar Stock

- To find the most similar stock based on the computed rolling window metric time series, the basic way is to perform the metric calculation for all stocks and then choose the max based on the similarity measure by some function that implements a way of calculating similarity between time series.

- A basic implemetation of a function to calculate similarity or (-distance) between 2 times series can be based on [`Pearson correlation`](https://en.wikipedia.org/wiki/Pearson_correlation_coefficient), which compares the patterns of fluctuation of the time serie and not the values.

- Here obviously we can't have a pre-built index that we can query and give us the closest time-series, mainly because we can't pre-calculate the metrics for all the stocks for all rolling-window possible numbers.\
First because this data is not meant to be static, but rather updated with new stock market numbers for each open market day.\
The second reason is because of the large number of time-series we should calculate: we need it for each stock (we have `3561` in our data and for each metric (5) and for each possible rolling-window (between 1 and 100 -> 91) and for each possible date(`504`) in our dataset => This results in `3561 * 5 * 504 * 100 = ~ 900M` unique metric to compute.\
The third reason is that it will be very complex to maintain an index on time series because we need first to create all possible time-series with all possible lengths (date ranges: 504) and maintain each in a separate index (we can use faiss for similarity search vectors indexes with custom similarity function)

- To solve the problem of re-calculating the the entire metric based on the rolling window we can use `pre-aggreation` and caching as described [here](#pre-aggregation). This will allow to have the metric time-series of each.

- One property of the problem at hand is that it can be `performed in parallel`. Once the target stock metric time series is calculated, both calculating the metric time series and the similarity to the target stock's one can be done for each stock in parallel. At the end we need to `aggregate` the results and return the max value.\ Here we can use a `map reduce` technology where
  - `map` is calculating similarity for each stock to our target stock.
  - `Reduce` is calculating the most similar => the min

- We can distribute the work with distributed computation technologies like `spark` or `dask`. These make it easy for the `reduce` part since it is supported out of the box (for spark the result will be reduced in the driver)\
We can also leverage An event based architecture where we create an event for each stock in a `queue` (AMAZON SQS or Tasks queue on GCP) and `cloud functions` (or cloud run) that will be `triggered based on the queue content` to calculate the metric and then the similarity and send the result to an aggregation service that can be a simple web app that caculates the maximum similarity on the fly based on the incoming post requests.\
The end choice of the technology will depend on the costs of different cloud infrastructure parts and the size of the data at hand.

- We can hit some bottelneck in terms of the number of connections to the DB, but we can use the techniques described [above](#many_queries) to serve many queries at once like connection pools and replication for the DB and horizontal scaling for the web app.

- This scheme illustrates the idea of distributing the calculation.
<img src="./docs/images/parallel_similarity.svg">

## Next steps:
- Add test coverage for the populator codebase `pipeline`.
- Add Continuous integration (CI) with Github actions to run all unit tests at each commit.

## Github Action Remark:
Actions are still failing:
For pre-commit hook jobs the problem should come from a bug in isort since the pre-commit is working fine locally:
```
➜  syrup_tech_take_home_test git:(master) ✗ pre-commit run --all-files
black....................................................................Passed
isort....................................................................Passed
Check python ast.........................................................Passed
Check docstring is first.................................................Passed
Debug Statements (Python)................................................Passed
Detect Private Key.......................................................Passed
Forbid new submodules....................................................Passed
Mixed line ending........................................................Passed
Trim Trailing Whitespace.................................................Passed
Fix End of Files.........................................................Passed
Tests should end in _test.py.............................................Passed
Check for added large files..............................................Passed
Check for case conflicts.................................................Passed
Check for merge conflicts................................................Passed
Check for broken symlinks............................(no files to check)Skipped
Fix double quoted strings................................................Passed
Check JSON...........................................(no files to check)Skipped
Pretty format JSON...................................(no files to check)Skipped
Check Yaml...............................................................Passed
Sort simple YAML files...............................(no files to check)Skipped
flake8...................................................................Passed
➜  syrup_tech_take_home_test git:(master) ✗
```

- For the api tests, there is some docker-compose config that I have to check, but tests run locally as described [here](#tests)
