# Celery Queue Setup for 100+ Users
The API and batch processes for heavy tasks like Weekly Letters and Daily KI Inference have been moved to Celery Tasks to prevent the Flask thread from blocking or getting timeout errors.

1. Ensure Redis is running (use homebrew if Mac: `brew install redis && brew services start redis`)
`redis-server`
2. Start the Celery Worker (In `backend` dir):
`celery -A celery_app worker --loglevel=info`

These will naturally batch process using available node capacity instead of trying to run everything simultaneously.

## Added Batch 
`celery_app.py: generate_weekly_letters_batch` task.

