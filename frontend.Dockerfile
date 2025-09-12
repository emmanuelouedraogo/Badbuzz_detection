# ---- Builder Stage ----
# This stage installs dependencies into a virtual environment
FROM python:3.12-slim as builder

WORKDIR /app

# Create a virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install the lightweight dependencies for the frontend
COPY requirements-frontend.txt .
RUN pip install --no-cache-dir -r requirements-frontend.txt


# ---- Final Stage ----
# This stage creates the final, smaller image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Create a non-root user for security
RUN useradd --create-home appuser
USER appuser

# Copy virtual env and application code from builder stage
COPY --from=builder /opt/venv /opt/venv
COPY streamlit_app.py .

# Activate the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Make port 8501 available
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]