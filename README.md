# Science (Medical) Surveyor

Collects data, and shows charts and articles in medical research areas. Particularly Pubtator's COVID-19
articles are indexed in this version.


## Get started

* Start Elasticsearch: `elasticsearch/run-elasticsearch-docker.sh`
* Download data: `./download-data-pubtator-covid-19.sh`
* Save into Elasticsearch: `./load-pubtator-covid-19-into-es.py`
* Run web server: `cd http-server && ./build-and-run-docker.sh`
* Open browser towards localhost:8080/pubtator/covid-19


## Design of web server

Data is pre-processed before entered into Elasticsearch, so very little processing is required in the web app.
The article search is (currently) a single html file (http-server/templates/research.html), which contain both
html and javascript for fetching the data and plot, and some minor click handing into the DOM.

Python uses the plotting-library Bokeh to generate the charts, and the web server Flask to produce end-points.
Flask uses Jinja2 as templating-library for the html. jQuery is used client-side to manipulate the DOM.


## Docker setup

Elasticsearch is started in a network called "backend". It's network alias is set to "elastic". When
`http-server.py` is started, it looks at the environment variable "ESHOST" to determine the hostname of the
Elasticsearch server. If "ESHOST" is not set, it uses "localhost".
