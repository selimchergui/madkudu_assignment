FROM quay.io/astronomer/astro-runtime:9.7.0
USER astro
RUN pip install dbt-redshift
RUN pip install apache-airflow-providers-amazon

USER root
RUN chown -R astro:astro /usr/local/airflow

USER astro