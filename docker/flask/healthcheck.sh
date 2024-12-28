#!/bin/bash

HTTP_CODE=$(curl -s -w "%{http_code}" http://localhost:8081/auth/health_check -o /dev/null)
if [ "$HTTP_CODE" = "200" ]; then
   exit 0
else
   exit 1
fi