#!/bin/bash

# Health check script for MariaDB

# Load environment variables with default values
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-3306}
DB_USER=${MYSQL_USER}
DB_PASSWORD=${MYSQL_PASSWORD}
DB_NAME=${MYSQL_DATABASE}

echo "Starting health check script..."
echo "DB_HOST=$DB_HOST"
echo "DB_PORT=$DB_PORT"
echo "DB_USER=$DB_USER"
echo "DB_PASSWORD=$DB_PASSWORD"
echo "DB_NAME=$DB_NAME"

while true; do
  echo "Checking MariaDB at $DB_HOST:$DB_PORT with user $DB_USER and database $DB_NAME"
  if mariadb -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" -e "USE $DB_NAME;" > /dev/null 2>&1; then
    echo "MariaDB is up - exiting health check"
    exit 0
  else
    echo "MariaDB is unavailable - sleeping"
    sleep 1
  fi
done
