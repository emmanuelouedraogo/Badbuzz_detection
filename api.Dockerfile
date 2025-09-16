# ---- Builder Stage ----
# This stage installs dependencies and downloads assets
FROM python:3.12-slim as builder

WORKDIR /app

# Install wget for downloading files
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python dependencies into the virtual environment
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Declare build arguments that will be passed from docker-compose
ARG MODEL_URL
ARG TOKENIZER_URL

# Create directory for the model and download files from the provided URLs
RUN mkdir -p /app/saved_model
RUN wget -O saved_model/best_gensim_bidirectional_gru_en_model.keras ${MODEL_URL}
RUN wget -O tokenizer.pickle ${TOKENIZER_URL}


# ---- Final Stage ----
# This stage creates the final, smaller image
FROM python:3.12-slim

WORKDIR /app

# Set TensorFlow log level to suppress INFO and WARNING messages (1=filter INFO, 2=filter WARNING, 3=filter ERROR)
ENV TF_CPP_MIN_LOG_LEVEL=2

# Create a non-root user for security
RUN useradd --create-home appuser
USER appuser

# Copy virtual env and models from builder stage
COPY --chown=appuser:appuser --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser --from=builder /app/saved_model /app/saved_model
COPY --chown=appuser:appuser --from=builder /app/tokenizer.pickle /app/tokenizer.pickle

# Copy the application's source code
COPY --chown=appuser:appuser app.py .

# Activate the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run the application using Gunicorn (production server)
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "app:app"]
