# Dockerfile

# Step 1: Use the official Python image with the desired version
FROM python:3.10-slim

# Step 2: Set the working directory in the container
WORKDIR /app

# Step 3: Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Step 4: Copy the requirements file and install dependencies
COPY  requirements.txt /app/
RUN   pip install --no-cache-dir -r requirements.txt

# Step 5: Copy the project files into the container
COPY . /app/

# Step 6: Expose the port Django runs on
EXPOSE 8000

# Step 7: Run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
