#FROM python:3
FROM python:3.7-buster

# Create app directory
WORKDIR /usr/src/app

RUN pip install numpy cython pandas pathlib scipy implicit matplotlib flask Response Flask-SQLAlchemy python-form Flask-WTF requests boto3

COPY . .

EXPOSE 5000

CMD [ "python", "Demonstrator.py", "--host", "0.0.0.0"]
