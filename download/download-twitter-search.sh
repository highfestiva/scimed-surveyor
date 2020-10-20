#!/bin/bash

./download-twitter-search.py --start-time "2020-10-15T16:00:00Z" --end-time "2020-10-20T11:00:00Z" --stride-time 30:00 --interval-limit 100 --search "ai (medicine OR healthcare OR ehealth OR telemedicine)"
