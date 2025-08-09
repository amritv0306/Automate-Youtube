# Step 1: Start with a base Python image
FROM python:3.11-slim-bookworm

# Step 2: Update packages and install FFmpeg
# The "apt-get upgrade -y" command patches the security vulnerabilities you saw.
RUN apt-get update && apt-get upgrade -y && apt-get install -y ffmpeg

# Step 3: Set the working directory inside the container
WORKDIR /app

# Step 4: Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy the rest of your project files into the container
COPY . .

# Step 6: Define the command to run when the container starts
CMD ["python", "final_pipeline.py"]