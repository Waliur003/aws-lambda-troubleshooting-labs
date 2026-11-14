import json
import logging
import os
import socket

import pg8000.dbapi

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Lambda Lab 07 started")

    host = os.environ["DB_HOST"]
    port = int(os.environ.get("DB_PORT", "5432"))
    database = os.environ["DB_NAME"]
    username = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]

    logger.info("Database connection test started")

    # Diagnostic: test TCP reachability first.
    try:
        with socket.create_connection(
            (host, port),
            timeout=4
        ):
            logger.info(
                "TCP connectivity to PostgreSQL succeeded"
            )

    except (socket.timeout, OSError) as exc:
        logger.exception("PostgreSQL TCP connection failed")

        return {
            "statusCode": 503,
            "body": json.dumps({
                "status": "failed",
                "stage": "tcp",
                "error_type": type(exc).__name__
            })
        }

    connection = None

    try:
        connection = pg8000.dbapi.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password,
            timeout=4
        )

        cursor = connection.cursor()

        cursor.execute(
            "SELECT current_database(), current_user, 1 + 1"
        )

        result = cursor.fetchone()

        logger.info("PostgreSQL SQL query succeeded")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "success",
                "database": result[0],
                "username": result[1],
                "calculation": result[2]
            })
        }

    except Exception as exc:
        logger.error(
            "PostgreSQL SQL connection or query failed: %s",
            type(exc).__name__
        )

        return {
            "statusCode": 503,
            "body": json.dumps({
                "status": "failed",
                "stage": "sql",
                "error_type": type(exc).__name__
            })
        }

    finally:
        if connection is not None:
            connection.close()
