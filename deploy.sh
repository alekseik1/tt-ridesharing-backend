#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

(
  cd "$DIR/.." || exit # Go to project dir.

  ssh $SSH_USERNAME@$SSH_HOSTNAME -o StrictHostKeyChecking=no <<-EOF
    cd $SSH_PROJECT_FOLDER
    git pull
    docker-compose pull
    docker-compose stop
    docker-compose -f docker-compose.prod.yml up -d --force-recreate
EOF
)