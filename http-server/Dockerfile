FROM python:3.8

RUN pip install --upgrade pip
RUN pip install flask pandas bokeh
RUN pip install requests flask-caching

ADD *.py /usr/local/
ADD templates/ /usr/local/templates/
ADD static/ /usr/local/static/
WORKDIR /usr/local
CMD ["./http-server.py"]
