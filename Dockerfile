# Dockerfile

# 1. Use Python 3.11 because scikit-learn 1.8.0 requires Python >= 3.11
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Prevent Python from writing .pyc files
#    and make stdout/stderr appear immediately in Railway logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4. Copy requirements first so Docker can cache dependency installation
COPY requirements.txt .

# 5. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the entire application into the container
COPY . /app

# 7. Document the application port
EXPOSE 8000

# 8. Start the Flask application
CMD ["python", "app.py"]