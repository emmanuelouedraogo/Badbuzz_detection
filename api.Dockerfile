# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Install wget for downloading files
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Declare build arguments that will be passed from docker-compose
ARG MODEL_URL
ARG TOKENIZER_URL

# Create directory for the model and download files from the provided URLs
RUN mkdir -p saved_model
RUN wget -O saved_model/best_gensim_bidirectional_gru_en_model.keras ${MODEL_URL}
RUN wget -O tokenizer.pickle ${TOKENIZER_URL}

# Copy only the application's source code
COPY app.py .

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run the application using Gunicorn (production server)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "600", "--preload", "app:app"]
