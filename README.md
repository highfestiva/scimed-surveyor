# Science (Medical) Surveyor

Collects data, and shows charts and articles in medical research areas. Particularly Pubtator's COVID-19
articles are indexed in this first version.


## Get started

* Build web server: `docker-compose build`
* Start Elasticsearch, nginx and web server: `docker-compose up -d`
* Download data: `cd download; ./download-data-pubtator-covid-19.sh`
* Save into Elasticsearch's DB: `cd download; ./load-pubtator-into-es.py --index pubtator-covid-19 --file data/litcovid2pubtator.json`
* Open browser towards localhost:8080/pubtator/covid-19


## Design of web server

Data is pre-processed before entered into [Elasticsearch](https://www.elastic.co/), so very little processing
is required in the web app. The article search is (currently) a single html file
([research.html](scimed-surveyor/blob/master/http-server/templates/research.html)), which contain both html and
javascript for fetching the data and plot, and some minor click handing into the DOM.

Python uses the plotting-library [Bokeh](https://bokeh.org/) to generate the charts, and the web server
[Flask](https://flask.palletsprojects.com/en/1.1.x/) to produce end-points. Flask uses
[Jinja2](https://jinja.palletsprojects.com/en/2.11.x/) as templating-library for the html.
[jQuery](https://jquery.com/) is used client-side to manipulate the DOM.


## [Docker](https://www.docker.com/) setup

[docker-compose](https://docs.docker.com/compose/) is used to start Elasticsearch, Kibana, the web server,
the reverse proxy (nginx), etc. Kibana is mapped in under /kibana/.


## Download and insert new PubTator topics

To get new a PubTator topic shown in the web server you need to do two things:

1. Download PubTator articles
2. Insert the downloaded articles into Elasticsearch

To download you move to the directory `./download/` and run for instance:

````bash
$ ./download-data-pubtator-search.py --limit 10000 prostate cancer
````

That script will save the 10,000 results into `download/data/prostate+cancer.json`. Normally the number of
results will be slightly less than 10,000, as not all PubMed articles are absorbed by PubTator.

To install those downloaded articles, run:

````bash
$ ./load-pubtator-data-into-es.py --index pubtator-prostate-cancer data/prostate+cancer.json
````

Approximate throughput of download is 170 articles/s. Elasticsearch insert throughput is approximately 570
articles/s. Go to http://host:port/pubtator/prostate-cancer to see the new topic.
