import logging
import docker
import requests
from dotenv import load_dotenv
from os import getenv
from sys import stderr, exit
from flask import Flask, abort, request
from json import loads, JSONDecodeError


logging.basicConfig(stream=stderr, level=logging.INFO)
load_dotenv()


def parse_bool(str):
    return str == 'True'


IMAGE_NAME = getenv('IMAGE_NAME')
if not IMAGE_NAME:
    logging.error("IMAGE_NAME must be set")
    exit(1)
CONTAINER_NAME = getenv('CONTAINER_NAME')
if not CONTAINER_NAME:
    logging.error("CONTAINER_NAME must be set")
    exit(1)
VIRTUAL_HOST = getenv('CONTAINER_VIRTUAL_HOST')
if not VIRTUAL_HOST:
    logging.error("CONTAINER_VIRTUAL_HOST must be set")
    exit(1)
LETSENCRYPT_HOST = getenv('CONTAINER_LETSENCRYPT_HOST')
if not LETSENCRYPT_HOST:
    LETSENCRYPT_HOST = VIRTUAL_HOST
NETWORK = getenv('NETWORK')

PORT = getenv('PORT')
if not PORT:
    logging.error("PORT must be set")
    exit(1)

DEBUG = getenv('DEBUG')
if DEBUG:
    DEBUG = parse_bool(DEBUG)
else:
    DEBUG = False

UUID = getenv('UUID')
if not UUID:
    logging.error("UUID must be set")
    exit(1)

client = docker.from_env()
client.containers.list()


def remove_containers():
    global IMAGE_NAME, client
    containers = client.containers.list(
        all=True, filters={'ancestor': IMAGE_NAME})
    [logging.info("Removing %s" % container.name) for container in containers]
    [container.remove(force=True) for container in containers]
    logging.info("Successfully removed containers")


def pull_image():
    global IMAGE_NAME, client
    logging.info("Pulling %s" % IMAGE_NAME)
    client.images.pull(IMAGE_NAME)
    logging.info("Successfully Pulled Image")


def create_new_container():
    global IMAGE_NAME, VIRTUAL_HOST, LETSENCRYPT_HOST, NETWORK, CONTAINER_NAME, client
    logging.info("Creating Container")
    container = client.containers.run(image=IMAGE_NAME,
                                      environment={
                                          "VIRTUAL_HOST": VIRTUAL_HOST, "LETSENCRYPT_HOST": LETSENCRYPT_HOST},
                                      network=NETWORK,
                                      name=CONTAINER_NAME,
                                      detach=True)
    logging.info("Successfully created container with name %s" %
                 container.name)


def call_api(url, status, description="Deployed"):
    logging.info("Calling API")
    r = requests.post(url=url, json={
        'state': status,
        'description': description,
        'context': "Continuous deployment on Falcon",
    })
    logging.info("Response data is %s" % r.json())


application = Flask(__name__)


@application.route('/<id>', methods=['GET', 'POST'])
def index(id):
    global UUID
    logging.info("Got request at /")
    if id != UUID:
        logging.error("UUID NOT EQUALS TO GIVEN ID")
        return ""
    try:
        callback_url = loads(request.get_data())['callback_url']
    except JSONDecodeError:
        logging.error("Error decoding JSON")
        return ""
    logging.info("Successfully passed checks")

    try:
        remove_containers()
        pull_image()
        create_new_container()
    except FileNotFoundError:
        logging.error("Docker not found!")
        exit(1)

    call_api(callback_url, status='success')
    return "success"


if __name__ == "__main__":
    try:
        remove_containers()
        pull_image()
        create_new_container()
    except FileNotFoundError:
        logging.error("Docker not found!")
        exit(1)
    logging.info("All systems operational, beginning application loop")
    application.run(debug=DEBUG, host='0.0.0.0', port=PORT)
