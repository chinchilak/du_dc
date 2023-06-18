FROM python:3.11
RUN apt-get update && \
    apt-get install -y \
        libgtk-3-dev \
        libnotify-dev \
        libgconf-2-4 \
        libnss3 \
        libxss1 \
        libasound2 \
        xvfb
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m playwright install
COPY app.py .
EXPOSE 8080
CMD ["python", "app.py"]