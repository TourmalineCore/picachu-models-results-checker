import os

results_host = os.getenv('RESULTS_HOST')

if not results_host:
    raise ValueError('You should specify RESULTS_HOST to be able to connect to host with models results.')