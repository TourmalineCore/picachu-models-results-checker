"""Сonfiguration
Use env var to override
"""
import os

ENV = os.getenv('FLASK_ENV')
DEBUG = ENV == 'development'

rabbitmq_host = os.getenv('RABBITMQ_HOST')
rabbitmq_username = os.getenv('RABBITMQ_DEFAULT_USER')
rabbitmq_password = os.getenv('RABBITMQ_DEFAULT_PASS')

rabbitmq_association_queue_name = os.getenv('RABBITMQ_ASSOCIATION_QUEUE_NAME')
models_queues_dlx = os.getenv('MODELS_QUEUES_DLX')


if not rabbitmq_host:
    raise ValueError('You should specify RABBITMQ_HOST to be able to connect to RabbitMQ.')

if not rabbitmq_username:
    raise ValueError('You should specify RABBITMQ_DEFAULT_USER to be able to connect to RabbitMQ.')

if not rabbitmq_password:
    raise ValueError('You should specify RABBITMQ_DEFAULT_PASS to be able to connect to RabbitMQ.')

if not rabbitmq_association_queue_name:
    raise ValueError('You should specify RABBITMQ_ASSOCIATION_QUEUE_NAME to be able to connect to queue with requests.')

if not models_queues_dlx:
    raise ValueError('You should specify MODELS_QUEUES_DLX to be able to connect to queue with requests.')


class RabbitMQConfigProvider:
    @staticmethod
    def get_config():
        return (
            rabbitmq_host,
            rabbitmq_username,
            rabbitmq_password,
        )
