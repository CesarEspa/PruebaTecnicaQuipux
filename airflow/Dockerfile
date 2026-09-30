# Partimos de la imagen oficial de Airflow y solo le agregamos las
# librerias que necesita nuestro DAG (pymongo, pandas, pyarrow).
# Usamos el archivo de "constraints" oficial para que pip instale
# versiones compatibles entre si y con Airflow (asi lo recomienda la
# documentacion de Airflow para extender su imagen).
FROM apache/airflow:2.9.3-python3.11

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.11.txt"
