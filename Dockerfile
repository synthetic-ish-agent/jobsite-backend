# Dockerfile

# 1. Use an official Python runtime as a parent image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Prevent Python from writing .pyc files to disc 
# and buffer stdout/stderr streams to make logs immediately available
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 4. Copy the requirements file and install dependencies
# This step is cached, so it only runs if requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the entire application code into the container
COPY . /app

# 6. Expose the port the application will run on
# Flask/SocketIO defaults to 8000 in your code
EXPOSE 8000

# 7. Define the command to run the application using Gunicorn 
# Gunicorn is a fast, stable, and production-ready WSGI server.
# We run the application instance 'app' defined in 'app.py'
# NOTE: We use Gunicorn to wrap the SocketIO server via 'eventlet' or 'gevent' for production.
# Your setup uses SocketIO, so we use the flask_socketio.run server for simplicity,
# but for true production scaling, Gunicorn with eventlet is better.
CMD ["python", "app.py"] 

# If you wanted to use Gunicorn/eventlet for production:
# RUN pip install eventlet
# CMD ["gunicorn", "app:socketio", "--bind", "0.0.0.0:8000", "-k", "eventlet"]