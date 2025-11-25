#!/bin/sh
# MkDocs healthcheck script
wget --no-verbose --tries=1 --spider http://localhost:8000/ || exit 1
