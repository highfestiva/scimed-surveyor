FROM python:3.8

ADD *.py .twitterkey.py .espassword /usr/local/
RUN mkdir -p /usr/local/data/
ADD autoupdate/*.py autoupdate/*.sh /usr/local/autoupdate/
WORKDIR /usr/local/autoupdate
ENV ESHOST=elastic
CMD ["./fetch-latest-ai-tweets.sh"]
