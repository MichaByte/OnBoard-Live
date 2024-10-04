FROM python:3.12-slim

EXPOSE 8000

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apt-get update

RUN apt-get install -y python3-opencv

RUN pip install --no-cache-dir -r requirements.txt

COPY schema.prisma .

ADD migrations .

RUN prisma generate

COPY main.py .

CMD [ "uvicorn", "main:api", "--log-level", "warning", "--workers", "4", "--host", "0.0.0.0", "--port", "8000" ]
