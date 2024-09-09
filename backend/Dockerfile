FROM python:3.12-slim

EXPOSE 8000

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apt-get update

RUN apt-get install -y python3-opencv

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py schema.prisma .

COPY migrations .

RUN prisma generate

CMD [ "fastapi", "run", "main.py" ]
