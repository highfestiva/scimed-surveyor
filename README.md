# Science (Medical) Surveyor

Collects data, and shows charts and articles in medical research areas. Particularly Pubtator's COVID-19
articles are indexed in this first version.


## Get started

* Start Elasticsearch: `elasticsearch/run-elasticsearch-docker.sh`
* Download data: `./download-data-pubtator-covid-19.sh`
* Save into Elasticsearch: `./load-pubtator-covid-19-into-es.py`
* Run web server: `cd http-server && ./build-and-run-docker.sh`
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

Elasticsearch is started in a [network](https://docs.docker.com/network/) called `backend`. It's network alias
is set to `elastic`. When `http-server.py` is started, it looks at the environment variable `ESHOST` to
determine the hostname of the Elasticsearch server. If `ESHOST` is not set, it uses `localhost`.
