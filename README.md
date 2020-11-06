# Science (Medical) Surveyor

Collects data, and shows charts and articles in medical research areas. Particularly PubTator articles
and tweets (on Twitter) are indexed in this first version.

The articles are presented by a web server. The web server is executed by [Docker Compose](https://docs.docker.com/compose/),
which also starts other applications (like a database).

Twitter data (medical/AI filter) is collected automatically by a task running in Docker Compose. The tweet-collecting
code is in `download/autoupdate/` and `download/*twitter*.py`. If you want to add a new topic from PubTator, you have
to run a couple of commands manually to first download, then inject into the database. See below for more info.

Each topic has an index of its own and is shown in a separate web page. Topics can have an url path like `/pubtator/cardiac-failure`
or `/twitter/tech`, which would be located in Elasticsearch indices `pubtator-cardiac-failure` and `twitter-tech`.

On each topic web page you can filter out which annotations you solely want to show. Such a filter can be compared with
another to see how they developed over the time. The system currently supports comparing two such filters.


## Geting started

In order to download and process PubTator articles, you need a Python environment setup and
this repository.

````bash
sudo me@host

pip3 install elasticsearch python-dateutil pytz requests spacy
python3 -m spacy install en_core_web_sm

# get the repo
git clone https://github.com/highfestiva/scimed-surveyor.git
cd scimed-surveyor/
````

The rest happens inside docker containers, so no need for runtime libraries.


### Setting Elasticsearch password

The default username is used by Elasticsearch, but the password must be set manually. Something like this:

````bash
echo "my-v3ry.s8rt_p4zzwrd" > download/.espassword`
````

That file, `.espassword`, is used in a number of places, but no more manual editing/copying should be required.


### Your first run

````bash
cd scimed-surveyor/

# build and run docker containers
./redeploy.sh

# download some articles
cd download
./download-data-pubtator-covid-19.sh

# save into elasticsearch
./load-pubtator-into-es.py --index pubtator-covid-19 --file data/litcovid2pubtator.json

# open browser towards localhost:8080/pubtator/covid-19
````


## Internal design of web server

The web server consists of 353 lines of Python code, 230 lines of HTML and 347 lines of CSS. A little JS
code is embedded in the HTML.

The web server shows pages with articles/tweets, and some categories (called "annotations"). Some of the
PubTator pages shows a map over which countries the articles were published in.

Data is pre-processed before entered into [Elasticsearch](https://www.elastic.co/), so very little processing
is required in the web app. The article search is (currently) a single html file
([research.html](http-server/templates/research.html)), which contain both html and
javascript for fetching the data and plots, and some minor click handing into the DOM.

There is also a separate web page for comparing annotations ([compare-annotations.html](http-server/templates/compare-annotations.html)),
and a landing page which loads all indices and default filters ([landing.html](http-server/templates/landing.html)).

Python uses the plotting-library [Bokeh](https://bokeh.org/) to generate the charts, and the web server
[Flask](https://flask.palletsprojects.com/en/1.1.x/) to produce end-points. Flask uses
[Jinja2](https://jinja.palletsprojects.com/en/2.11.x/) as templating-library for the html.
[jQuery](https://jquery.com/) is used client-side to manipulate the DOM.

The Country shape data was downloaded 2020-10-26 from [github](https://raw.githubusercontent.com/dmillz/misc/master/shapefiles/ne_10m_admin_0_countries_lakes-EPSG_3857.zip).
That shape has a EPSG:3857 projection (also called "WGS 84" and "Pseudo-Mercator"), which is what's used in
most online maps. The original shape can be downloaded from [Natural Earth](https://www.naturalearthdata.com/downloads/110m-cultural-vectors/).
The shape data is further pre-processed by the script [map2json.py](http-server/map2json.py)
which extracts the relevant countries and stores their shapes in `http-server/data/`. The [map2json.py](http-server/map2json.py)
script requires [geopandas](https://geopandas.org/).


### Configuration of pages

Apart from the main topic pages, there is a landing page and an annotation comparison page. The main topic
pages are linked from the landing page. This is also where they get their default filters and comparisons.
One link to a topic could be http://host:port/pubtator/pancreatic-cancer?filter=%5B%7B%22medicine%22%3A%5B%22surgery%22%5D%7D%2C%7B%22chemical%22%3A%5B%22gemcitabine%22%5D%7D%5D
, where the filter parameter decodes to `[{"medicine":["surgery"]},{"chemical":["gemcitabine"]}]`.

When clicking on the link, the user is taken to a topic page where she is free to modify her session filters
using the [x] and [Compare] buttons. All filters are carried by the URL, nothing is stored in cookies or
otherwise.

The default filters and other settings are configurable in [http-server/conf/settings.py](http-server/conf/settings.py).
That file is loaded runtime, and changing it does not require you to re-deploy the docker containers. This is
what `settings.py` look like:

````python
{
    '<default>': {
        'exclude-annotations': ['species'],
        'exclude-labels': {'disease': ['Learning Disabilities']},
    },

    'twitter-tech': {
        'filter': [{'term':['Health']}, {'tech':['ehealth']}],
        'period': 60*60*1000,
        'map': False,
    },

    'pubtator-pancreatic-cancer': {
        'filter': [{'medicine':['surgery']}, {'chemical':['gemcitabine']}],
        'exclude-annotations': ['species', 'cell-line', 'ai', 'mutation'],
    },
}
````

The `<default>` key is what's used if a sub-key of a specific topic is missing. The `filter` key contains
the default filter (linked from the landing page). There are a couple of keys worth mentioning:

* `period` defaults to daily, but for Twitter we use hourly.
* `map` defaults to True, but for Twitter there is no country metadata.


## Docker setup

[Docker Compose](https://docs.docker.com/compose/) is used to start Elasticsearch, Kibana, the web server,
the reverse proxy (nginx), the twitter updater, etc. Kibana is mapped in under /kibana/ by nginx.

Docker Compose starts a number of containers, but allows you to have dependencies and share network between
them without additional setup. It's a beautiful way to build and run the five applications with very little
overhead. See [docker-compose.yml](docker-compose.yml).

Some data is mapped to the host file system, such as the Elasticsearch database. That way, it does not need
to be re-created if the elastic docker container is restarted. Other files that are kept in the host file
system include `http-server/conf/`, `download/autoupdate/data/` (where the Twitter history is kept) and
`nginx/nginx.conf`. The configuration files are kept on the host filesystem so no docker rebuild is
required to update the configurations (`git pull` or local edit is enough).

Elasticsearch, Kibana and nginx use default docker setup, while http-server and twitter-updater require a
Dockerfile each ([http-server/Dockerfile](http-server/Dockerfile) and
[download/autoupdate/Dockerfile](download/autoupdate/Dockerfile)).


# nginx setup

[nginx](https://www.nginx.com/) is a reverse proxy, used to map Elasticsearch and Kibana into the same
port as http-server, so they're reachable from internet. The configuration is kept in the file [nginx.conf](nginx/nginx.conf).

Everything is currently running on port 8080. To instead run on 80, simply update [docker-compose.yml](docker-compose.yml).


## Download and inject new PubTator topics

Code for downloading and loading into Elasticsearch consists of 471 lines of Python code.

To get new a PubTator topic shown in the web server you need to do two things:

1. Download PubTator articles
2. Pre-process and insert the downloaded articles into Elasticsearch

To download:

````bash
cd download/
./download-data-pubtator-search.py --limit 10000 prostate cancer
````

That script will save the first 10,000 results into `download/data/prostate+cancer.json`. Normally the
number of results will be slightly less than 10,000, as not all PubMed articles are absorbed by PubTator.

To install those downloaded articles, run:

````bash
./load-pubtator-data-into-es.py --index pubtator-prostate-cancer data/prostate+cancer.json
````

Approximate throughput of download is 170 articles/s. Elasticsearch insert throughput is approximately 570
articles/s. Go to http://host:port/pubtator/prostate-cancer to see the new topic.

If you wish to tag the data with Spacy's organization resolution, add a `--tag-organizations` switch:

````bash
./load-pubtator-data-into-es.py --index pubtator-prostate-cancer --tag-organizations data/prostate+cancer.json
````

Note though that letting Spacy categorize all article data is both slow and unreliable. For example, the
most common organization listed in the tech topics is CNN, which certainly is short for Convolutional
Neural Network in 100% of the cases.


## Inner workings of Twitter updater

New Twitter data is downloaded every hour by the shell script [download/autoupdate/fetch-latest-ai-tweets.sh](download/autoupdate/fetch-latest-ai-tweets.sh).
Currently that script and the related python scripts are made for tweets only, but could be adapted for
any kind of document.

The shell script runs in infinite loop which sleeps until a couple of minutes past every hour, then
looks into the Elasticsearch index to see what hour the latest tweet were registered. That is used as
a starting-point and each half-hour (`--stride-time 30:00`) since that time is downloaded. (The reason
I chose half-hours is that Twitter imposes a download limit per period of 100 tweets, and for our
current "AI" use 30 minutes is well in range without generating much overhead.)

Only Twitter supports incremental Elasticsearch index updates. The PubTator load script always deletes
the old index before inserting new data.


## How to update the http-server code

````bash
# edit server code
vim http-server/http-server.py

# push to github
git commit -m "Fix something" -a
git push

# fetch it on the server
ssh user@host
cd scimed-surveyor/
git pull

# build and restart those affected
./redeploy.sh
````

That same procedure applies to updating the twitter-updater code. If you only update [settings.py](http-server/conf/settings.py)
or [nginx/conf/nginx.conf](nginx/conf/nginx.conf) you can skip the last re-deploy step.


# Backing up Elasticsearch data

Copy the folder `elasticsearch-data/` and all it's subfolder somewhere safe, and you're done.


## Improvements

It's currently slow to insert a lot of article data into the Elasticsearch database. I tried using bulk
updates, but wasn't able to. Fixing that would probably speed up the process when handling tens of
thousands of documents.

Some caching (RAM) is added internally in [http-server.py](http-server/http-server.py),
and a little in nginx, but more could probably be done to improve performance.

Performance when loading tens of thousands of articles is bad. Improvements are probably mostly found in
Elasticsearch indexing and Bokeh use.

The map is really slow. One reason is that the country geometry definitions have too high resolution,
for instance downloading 55 countries yields a 5.9 MB gzipped JSON, or 200 times bigger than a time
series on 20k articles. That high resolution also makes zooming/panning the map an excrutiating
experience.
