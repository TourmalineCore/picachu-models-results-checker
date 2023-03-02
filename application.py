import json
import logging
import time

from flask import Flask
from flask_migrate import upgrade as _upgrade
from pika import ConnectionParameters, PlainCredentials, BlockingConnection, BasicProperties


import requests

from models_results_checker.commands.new_photo_id_command import NewPhotoIdCommand
from models_results_checker.config.host_config import results_host
from models_results_checker.config.rabbitmq_config import rabbitmq_host, rabbitmq_username, rabbitmq_password, \
    rabbitmq_association_queue_name, rabbitmq_models_queues_dlx
from models_results_checker.domain import PhotoIds
from models_results_checker.domain.data_access_layer.build_connection_string import build_connection_string
from models_results_checker.domain.data_access_layer.db import db, migrate
from models_results_checker.queries.photo_query import CheckPhotoQuery


parameters = ConnectionParameters(
    host=rabbitmq_host,
    credentials=PlainCredentials(rabbitmq_username, rabbitmq_password),
)


def ping_results_service():
    url = f'{results_host}/results-service/results'

    connection = BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(
        queue=rabbitmq_association_queue_name,
        arguments={
            "x-dead-letter-exchange": rabbitmq_models_queues_dlx,
            "x-dead-letter-routing-key": rabbitmq_association_queue_name
        },
        durable=True,  # need to persist the queue that should survive the broker restart
        exclusive=False,  # any consumer can connect to the queue, not only this one
        auto_delete=False,  # don't delete the queue when consumer disconnects
    )

    while True:
        response = requests.get(url)
        photos_data = json.loads(response.text)

        for photo_data in photos_data:
            if CheckPhotoQuery().by_id(photo_data["photo_id"]) is not None:
                continue

            logging.info(f'New photo with id: {photo_data["photo_id"]}')

            try:
                channel.basic_publish(
                    exchange='',
                    routing_key=rabbitmq_association_queue_name,
                    body=json.dumps(photo_data),
                    properties=BasicProperties(
                        delivery_mode=2,
                    )
                )
                logging.warning(f'Message with photo_id: {photo_data["photo_id"]} published')

            except Exception:
                logging.warning('Aborting...')
                connection.close()
                continue

            photo_id_entity = PhotoIds(id=photo_data["photo_id"])
            NewPhotoIdCommand().add_photo_id(photo_id_entity)
            logging.info(f'PhotoId inserted to db: {photo_data["photo_id"]}.')

        time.sleep(10)


def create_app():
    """Application factory, used to create application"""
    app = Flask(__name__)
    app.config.from_object('models_results_checker.config.flask_config')

    # without this /feeds will work but /feeds/ with the slash at the end won't
    app.url_map.strict_slashes = False

    app.config['SQLALCHEMY_DATABASE_URI'] = build_connection_string()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    # runs pending migrations
    with app.app_context():
        _upgrade()

    ping_results_service()
