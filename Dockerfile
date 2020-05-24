FROM python:3.7-slim-buster

# Load and cache requirements
ADD requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY ./ /app
RUN chmod +x /app/wait-for-it.sh

ENTRYPOINT ["./entrypoint.sh"]
