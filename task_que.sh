#!/bin/bash
celery -A app.celery.celery worker --loglevel=info