FROM python:3.8

RUN pip install --upgrade pip
RUN pip install flask pandas bokeh
RUN pip install elasticsearch requests flask-caching

ADD *.py .espassword /usr/local/
ADD templates/ /usr/local/templates/
ADD static/ /usr/local/static/
ADD data/ /usr/local/data/
WORKDIR /usr/local
ENV ESHOST=elastic
CMD ["./http-server.py"]
#CMD ["/bin/bash"]
