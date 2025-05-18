FROM python:3.13.2-bullseye

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    python3-dev \
    libasound-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY requirements.txt ./
# Install dependencies with extra packages needed for audio processing
RUN pip install -r requirements.txt

# Debug command to verify installation
RUN pip list

COPY . .

EXPOSE 8000

# Use uvicorn to run the FastAPI application with debug logging
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug" ]
