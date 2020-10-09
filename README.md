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
