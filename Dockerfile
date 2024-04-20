FROM python:3.7

WORKDIR src/myflask
ENV FLASK_APP=app.py
COPY . /src/myflask
RUN pip install -r requirements.txt


EXPOSE 5000
CMD ["flask", "run", "-h", "0.0.0.0"]