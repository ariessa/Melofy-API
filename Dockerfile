FROM python:3.7.10-slim-buster
RUN apt-get update -y && apt-get install -y \
build-essential \
libasound2-dev \
libjack-dev \
portaudio19-dev \
libsndfile1
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5000
ENTRYPOINT ["gunicorn"]
CMD ["app:app"]