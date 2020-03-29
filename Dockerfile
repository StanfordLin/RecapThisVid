FROM python:3

WORKDIR /app

COPY /Backend /app

RUN pip install -r requirements.txt

CMD ["python", "asyncsetup.py"]