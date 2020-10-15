#!/bin/bash

./download-twitter-search.py --start-time "2020-10-08T12:00:00Z" --end-time "2020-10-08T18:00:00Z" --stride-time 15:00 --interval-limit 10 --search "ai (medicine OR healthcare OR ehealth OR telemedicine)"
