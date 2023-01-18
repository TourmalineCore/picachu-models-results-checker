import json
import logging
import time

from flask import Flask, Blueprint
from flask_migrate import upgrade as _upgrade
from pika import ConnectionParameters, PlainCredentials, BlockingConnection, BasicProperties

from commands.new_photo_id_command import NewPhotoIdCommand
from config import models_queues_dlx, RabbitMQConfigProvider, rabbitmq_association_queue_name
from domain import PhotoIds
from domain.dal import db, migrate, build_connection_string

import requests

from queries.photo_query import CheckPhotoQuery

(
    rabbitmq_host,
    rabbitmq_username,
    rabbitmq_password,
) = RabbitMQConfigProvider.get_config()

parameters = ConnectionParameters(
    host=rabbitmq_host,
    credentials=PlainCredentials(rabbitmq_username, rabbitmq_password),
)


def ping_server():
    url = 'http://picachu-api:5000/api/labels'

    connection = BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(
        queue=rabbitmq_association_queue_name,
        arguments={
            "x-dead-letter-exchange": models_queues_dlx,
            "x-dead-letter-routing-key": rabbitmq_association_queue_name
        },
        durable=True,  # need to persist the queue that should survive the broker restart
        exclusive=False,  # any consumer can connect to the queue, not only this one
        auto_delete=False,  # don't delete the queue when consumer disconnects
    )

    while True:
        response = requests.get(url)
        photo_data = json.loads(response.text)

        for item in photo_data:
            if CheckPhotoQuery().by_id(item["photo_id"]) is not None:
                continue

            logging.info(f'New photo with id: {item["photo_id"]}')

            try:
                channel.basic_publish(
                    exchange='',
                    routing_key=rabbitmq_association_queue_name,
                    body=json.dumps(item),
                    properties=BasicProperties(
                        delivery_mode=2,
                    )
                )
                logging.warning(f'Message with photo_id: {item["photo_id"]} published')

            except Exception:
                logging.warning('Aborting...')
                connection.close()
                continue

            photo_id_entity = PhotoIds(id=item["photo_id"])
            NewPhotoIdCommand().add_photo_id(photo_id_entity)
            logging.info(f'PhotoId inserted to db: {item["photo_id"]}.')

        time.sleep(10)


def create_app():
    """Application factory, used to create application"""
    app = Flask(__name__)
    app.config.from_object('config')

    # without this /feeds will work but /feeds/ with the slash at the end won't
    app.url_map.strict_slashes = False

    app.config['SQLALCHEMY_DATABASE_URI'] = build_connection_string()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    # runs pending migrations
    with app.app_context():
        _upgrade()

    ping_server()
