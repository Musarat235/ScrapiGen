FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (if not fully covered by base image, but usually base image has them)
# The base image includes browsers, but running this ensures matching versions if requirements.txt differs
RUN playwright install --with-deps

# Copy the rest of the application
COPY . .

# Expose the API port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
