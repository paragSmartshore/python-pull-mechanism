# python-pull-mechanism

## Start the server with:

`docker compose up`

## Incase of any issues or if a new dependency is installed while starting up the project:

`docker compose build`

## Command to test fastapi on a particular file:

`fastapi dev app/main.py`

## To install a new package:

- First make sure there is a virtual environment present and also make sure the correct one is selected before installing anything.
- pip install [name-of-the-package]

## to list all the topics created by SNS

docker exec -it <container-id> awslocal sns list-topics
