FROM python:3.7-slim-buster

# Load and cache requirements
ADD requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt

# Upload whole application
ADD . /app
# TODO: read environment from config
ENV FLASK_ENV "development"

EXPOSE 5000
CMD ["flask", "run", "--host", "0.0.0.0"]
