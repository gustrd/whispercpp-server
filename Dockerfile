FROM python:bullseye

RUN apt-get update && \
    apt-get install -y python-dotenv && \   
    apt-get install -y ffmpeg && \
    apt-get install -y nodejs npm && \
    apt-get upgrade && \
    rm -rf /var/lib/apt/lists/*

RUN npm install -g localtunnel

WORKDIR /server

COPY . /server

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8010

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]