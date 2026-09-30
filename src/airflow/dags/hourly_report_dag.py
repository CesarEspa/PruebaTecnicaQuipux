"""
DAG de Airflow: genera un reporte consolidado de sismos cada hora.

Usamos la "TaskFlow API" de Airflow (los decoradores @dag y @task) porque
hace que cada tarea sea simplemente una funcion normal de Python que
recibe y devuelve datos; Airflow se encarga solo de pasar esos datos de
una tarea a otra (esto se llama XCom).

El flujo tiene exactamente los 3 pasos que pide el enunciado:
1. read_events       -> lee los sismos guardados en la ultima hora.
2. generate_report   -> calcula el reporte consolidado.
3. persist_report    -> guarda el reporte en Mongo y en un Parquet.
"""
from datetime import datetime, timedelta

import pendulum
from airflow.decorators import dag, task

from src.services.reporting_service import (
    build_report,
    export_events_to_parquet,
    read_events_for_window,
    save_report,
)

default_args = {
    "owner": "quipux",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}


@dag(
    dag_id="hourly_earthquake_report",
    description="Genera un reporte consolidado de sismos cada hora",
    schedule="@hourly",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    default_args=default_args,
    tags=["earthquakes", "reporting"],
)
def hourly_earthquake_report_dag():

    @task
    def read_events(data_interval_start=None, data_interval_end=None) -> list[dict]:
        """
        Paso 1: lee de Mongo los sismos de la hora que le toca procesar a esta
        ejecucion del DAG.

        data_interval_start / data_interval_end los inyecta Airflow
        automaticamente: son el inicio y el fin de la hora para la que se
        esta corriendo esta ejecucion (no simplemente "la hora actual"),
        que es lo correcto para que un DAG horario funcione bien incluso si
        se ejecuta tarde o se vuelve a correr manualmente.
        """
        events = read_events_for_window(data_interval_start, data_interval_end)

        # XCom guarda los datos como JSON, asi que convertimos el datetime
        # a texto antes de devolverlo.
        return [
            {
                "event_id": event["event_id"],
                "magnitude": event["magnitude"],
                "location": event["location"],
                "event_time": event["event_time"].isoformat(),
            }
            for event in events
        ]

    @task
    def generate_report(events: list[dict], data_interval_start=None) -> dict:
        """Paso 2: calcula total de sismos, magnitud promedio/maxima y top de ubicaciones."""
        report = build_report(events, report_date=data_interval_start)
        report["report_date"] = report["report_date"].isoformat()
        return report

    @task
    def persist_report(report: dict, events: list[dict]) -> None:
        """Paso 3: guarda el reporte en 'hourly_reports' y una copia en Parquet."""
        report_to_save = dict(report)
        report_to_save["report_date"] = datetime.fromisoformat(report["report_date"])

        save_report(report_to_save)
        export_events_to_parquet(events, report_to_save["report_date"])

    events = read_events()
    report = generate_report(events)
    persist_report(report, events)


hourly_earthquake_report_dag()
