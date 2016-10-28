# -*- coding: utf-8 -*-
"""
This is a simple Flask app that uses Authomatic to log users in with Facebook Twitter and OpenID.
"""

from flask import Flask, render_template, request, make_response, session, jsonify, g
import urllib
from authomatic import Authomatic
from authomatic.adapters import WerkzeugAdapter
import sqlite3
import urllib, urllib2
import time, json, math, sys
import oauth2 as oauth
import feedparser

from config import CONFIG

app = Flask(__name__)

app.secret_key = 'Pootchie'

@app.route('/sov/api/v1.0/sov_calc', methods=['GET'])
def sov_calc():

    competitors = request.args.get('competitors')
    topics = request.args.get('topics')

    competitors_sep = competitors.split(',')
    topics_sep = topics.split(',')

    CONSUMER_KEY = "NqDN6RTFyJeuMa6P8nUFFQ"
    CONSUMER_SECRET = "6KWDDW889GczHXaQYRDlerLqOo91ZAF0OLtmypIlGFo"
    ACCESS_KEY = "14401550-npXqDQ7e2uUnfIni2onJ5pac0Pgesq41vioZLz0Sg"
    ACCESS_SECRET = "24VHJg8LQyBujVEpSoNG2ZxSWHwu7rXuR8iqTZVATw4N7"

    consumer = oauth.Consumer(key=CONSUMER_KEY, secret=CONSUMER_SECRET)
    access_token = oauth.Token(key=ACCESS_KEY, secret=ACCESS_SECRET)
    client = oauth.Client(consumer, access_token)


    topics_string =' OR '.join(topics_sep)
    
    num_comps = 0
    cmentions = [0,0,0,0]


    for competitor in competitors_sep:
        search_string_comp1 = 'https://api.twitter.com/1.1/search/tweets.json?count=100&q=' + urllib.quote_plus(competitor) + ' AND (' + topics_string + ')'
        
        timeline_endpoint1 = search_string_comp1
        new_timeline_endpoint1 = timeline_endpoint1
        
        more_results_left = True
        c1mentions = 0
        i = 0
        while more_results_left == True:
            response, data = client.request(new_timeline_endpoint1)
            results = json.loads(data)
            c1mentions = c1mentions + len(results['statuses'])
            print str(c1mentions) + ' so far'
            cmentions[num_comps] = c1mentions
            if len(results['statuses']) > 1:
                for statuses in results['statuses']:
                    max_id = statuses['id']
                new_timeline_endpoint1 = timeline_endpoint1 + ' &max_id='+ str(max_id)
                more_results_left = True
                i=i+1
                if i == 20:
                    num_comps = num_comps + 1
                    break
            else:
                'print no more results'
                num_comps = num_comps + 1
                more_results_left = False


    

    total_mentions = cmentions[0] + cmentions[1] + cmentions[2] + cmentions[3]
    if total_mentions == 0:
        total_mentions = 1


    sov_calc = []
    num_comps = 0
    for competitor in competitors_sep:
        sov_calc.append({
        'percentage': round(float(cmentions[num_comps])/total_mentions,2),
        'competitor': competitor,
        })
        num_comps = num_comps + 1

    return jsonify({'sov_calc': sov_calc})





# Run the app.
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
