# Madkudu Assignment Response

The requested assignment is about designing and documenting an MVP about a data pipeline that process and expose data for performing efficient data analyses
<!-- TOC -->
  * [Prerequisites:](#prerequisites-)
    * [Init Airflow Astro environment](#init-airflow-astro-environment)
  * [Suggested pipeline architecture:](#suggested-pipeline-architecture-)
  * [Other possible designs/tools](#other-possible-designstools)
    * [Snowflake](#snowflake)
    * [AWS Athena + Glue](#aws-athena--glue)
  * [Urgent evolutions](#urgent-evolutions)
    * [Password management:](#password-management-)
    * [Incremental update:](#incremental-update-)
    * [DBT dynamic staging code:](#dbt-dynamic-staging-code-)
  * [Other evolutions:](#other-evolutions-)
    * [Ingest dimension tables:](#ingest-dimension-tables-)
    * [Data validation tests:](#data-validation-tests-)
    * [Data lineage](#data-lineage)
<!-- TOC -->
## Quick start:
- Install (if it's not the case) Docker-compose using offical [Docker Docs](https://docs.docker.com/compose/install/)
- Download and install [Astro CLI](https://docs.astronomer.io/astro/cli/install-cli)
- Clone the [current repository](https://github.com/selimchergui/madkudu_assignment).
- Change passwords in file **airflow_setting.yaml** and **dbt/profile.yml** with valid ones.
- Initiate the pipeline: `astro dev start` , you may need sudo if docker is a root only command.
- Connect to Airflow (localhost:8080) using default credentials and run [pipeline_orchestrator](http://localhost:8080/dags/pipeline_orchestrator) DAG.


## Suggested pipeline architecture:

![](/home/selim/Documents/Perso/madkudu/madkudu_assignment/images/MK_pipeline_design.jpg)

Since the data product is designed to expose analytics dashboard, OLAP databases are more suited for this use case than the OLTP kind.
**Cloud Data Warehouses** (like Snowflake, Redshift or BigQuery) are a good fit. Indeed, these tools are performant, highly scalable and have a lot of useful embedded features.
I choosed to use **Redshift** since the integration is simple and efficient with S3 service.

Data are uploaded monthly into S3. It's stored in a separate S3 key YYYY/mm/event.csv
Event's timestamp is in date format (YYYY/MM/DD), means that we can have daily statistics.
**Airflow** is a good orchestrator for this use case. We can use Airflow pre-built Operators to interact with S3 and Redshift to keep data up-to date
I choosed to use **Airflow Astronomer** distribution since it's very is to setup this tools (you don't have to configure Airflow component)

Finally, I used **DBT** to transform and test data inside Redshift. This framework is good way to organise data transformation pipeline inside a Datawarehouse.
It enriches SQL queries based with script code, offering a lot more capabilities.

Once data processed and prepared, dashboard in front app can be fed with data from Datawarehouse tables 
## Other possible designs/tools
### Snowflake
Snowflake is a well known tool, it's can easily ingest data from S3 and offer a lot out-of-the-box feature

### AWS Athena + Glue
Glue is a good serverless service where we can run Spark code. We can build an S3 based pipeline where data is read from input bucket, processed throw Glue workers and precomputed stats are then written into an output bucket.
Madkudu front app (or thrid-party tools like PowerBI or Tableau) can use data in output bucket through JDBC connector.

## Urgent evolutions
### Password management:
In current stack, passwords are used directly from configuration files and environment variables. This is not a good practice. Secret management tools like Hashcorp Vault or AWS Secret Manager should be used instead.

### Incremental update:
Current Airflow DAG doesn't check if data was updated since last DAG run or not. It reset target table in redshift each time. A more effecient way is to check S3 object update date first to target only new inserted or updated objects.

### DBT dynamic staging code:
I choosed to have a table per month for source and staging layer. The code need to be updated at least each month to be able to handle new objects.
This can be done using Airflow. In fact, we can add a task in the current DAG that update dbt code each time a new object in S3 is uploaded.


## Other evolutions
### Dimension tables:
We ingest additional dimension tables containing information about client, companies, etc...
These tables will be merged with events table to enrich current dashboard and offer more capabilities.

### Data validation tests:
Current tests (primary key unicity + none null) are good but do not sufficient for data integrity.
More advanced test should be added for example to check ip column or if action column make sense.

### Data lineage
We need to trace and monitor data as it moves through each stage of our pipeline.
To be able to do so, monitoring tools like Prometheus and/or Grafana can be used. 