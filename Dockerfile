FROM python:3.11-slim

# Install system dependencies for pdf->image and tesseract OCR
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       poppler-utils \
       tesseract-ocr \
       libsm6 libxrender1 libfontconfig1 libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
