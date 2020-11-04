FROM python:3.8

RUN pip install --upgrade pip
RUN pip install elasticsearch python-dateutil pytz requests
RUN pip install spacy
run python -m spacy download en_core_web_sm

ADD *.py *.sh .twitterkey.py .espassword /usr/local/
WORKDIR /usr/local
CMD ["./fetch-latest-ai-tweets.sh"]
