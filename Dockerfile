FROM python:3.8

RUN pip install --upgrade pip
COPY requirements.txt /
RUN pip install -r requirements.txt
COPY . /app
WORKDIR /app

RUN apt-get update
RUN apt-get install -y ffmpeg

CMD ["python", "-u", "main.py"]
