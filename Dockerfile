FROM python:3.12.6

RUN pip install --upgrade pip
COPY requirements.txt /
RUN pip install -r requirements.txt
COPY . /app
WORKDIR /app

CMD ["python", "-u", "main.py"]
