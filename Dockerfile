FROM python:3.7-slim-buster

# Load and cache requirements
ADD requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
# Upload whole application
ADD . /app

ENTRYPOINT ["/app/entrypoint.sh"]
