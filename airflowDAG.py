from airflow import DAG
from datetime import timedelta
from airflow.utils.dates import days_ago
from airflow.providers.google.cloud.operators.dataproc import ClusterGenerator
from airflow.providers.google.cloud.operators.dataproc import DataprocCreateClusterOperator
from airflow.providers.google.cloud.operators.dataproc import DataprocSubmitJobOperator
from airflow.providers.google.cloud.operators.dataproc import DataprocDeleteClusterOperator
from airflow.operators.bash import BashOperator

#change to your configuration here
REGION = 'asia-east2'
PROJECT_ID = 'nimble-valve-389007'
CLUSTER_NAME = 'zhun-demo-cluster-7ui84qq2'
extract_DB = 'gs://process-data-bucket/notebooks/jupyter/queryDB.ipynb'
extract_API = 'gs://process-data-bucket/notebooks/jupyter/api_extract.ipynb'
processing = 'gs://process-data-bucket/notebooks/jupyter/Processing.ipynb'


CLUSTER_CONFIG = ClusterGenerator(
    project_id=PROJECT_ID,
    cluster_name = CLUSTER_NAME,
    region = REGION,
    enable_component_gateway=True,
    optional_components = ['JUPYTER'],
    storage_bucket = 'process-data-bucket',
    num_masters = 1,
    master_machine_type = 'n1-standard-4',
    master_disk_size = 30,
    num_workers = 3,
    worker_machine_type = 'n2-standard-2',
    worker_disk_size = 30,
    image_version = '2.0-debian10',
    service_account_scopes = 'https://www.googleapis.com/auth/cloud-platform',
).make()


with DAG(
    "bookData-Processing",
    description='DAG to processing data and stored it in bq',
    start_date=days_ago(1),
    schedule_interval= None,
) as dag:
    
    CREATE = DataprocCreateClusterOperator(
            task_id="create_cluster",
            project_id=PROJECT_ID,
            cluster_config=CLUSTER_CONFIG,
            region= REGION,
            cluster_name=CLUSTER_NAME,
    )   

    DB = DataprocSubmitJobOperator(
            task_id="extract_DB", 
            job=extract_DB, 
            region=REGION, 
            project_id=PROJECT_ID
    ) 

    API = DataprocSubmitJobOperator(
            task_id="extract_API", 
            job=extract_API, 
            region=REGION, 
            project_id=PROJECT_ID,
    ) 
    
    PROCESSING = DataprocSubmitJobOperator(
            task_id="Processing", 
            job=processing, 
            region=REGION, 
            project_id=PROJECT_ID,
    ) 
    
    DELETE = DataprocDeleteClusterOperator(
            task_id="delete_cluster", 
            project_id=PROJECT_ID, 
            cluster_name=CLUSTER_NAME, 
            region=REGION,
    )

    BQ = BashOperator(
        task_id = "bqload" ,
        bash_command = "bq load \
                        --autodetect \
                        --source_format=CSV \
                        transaction.transaction_data \
                        gs://process-data-bucket/output/audible_data.csv"
    )

CREATE >> [API,DB] >> PROCESSING >> DELETE >> BQ
