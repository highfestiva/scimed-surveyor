#!/bin/bash

export index='twitter-tech'

while :
do
	# check db and clock to find start and end time
	last_t=`./lookup-twitter-last-es-hour.py --index ${index}`
	start_t=$(date -d@$(($(date -d ${last_t//Z/:00Z} +%s) + 3600)) -u -Ihours)
	end_t=`date -u -Ihours`
	echo "Downloading tweets between ${start_t} and ${end_t}."
	rm data/twitter.json
	#./download-twitter-search.py --start-time "$start_t" --end-time "$end_t" --stride-time 30:00 --interval-limit 100 --search "ai (medicine OR healthcare OR ehealth OR telemedicine)"
	#./load-twitter-data-into-es.py --index twitter-tech
	#cat data/twitter.json >> data/orig_twitter.json
	# wait until next time
	seconds_til_next_hour=$(($(date -d $(date -Ihours) +%s) + 3600 + 120 - $(date +%s))) # wait a couple minutes extra
	echo "Sleeping $seconds_til_next_hour seconds until next Twitter update."
	sleep $seconds_til_next_hour
done
