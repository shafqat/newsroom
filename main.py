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


from config import CONFIG

app = Flask(__name__)

app.secret_key = 'Pootchie'
DATABASE = 'newsroom.db'
#for prod uncomment next line
#DATABASE = '/var/www/HackDay/newsroom.db'

#there is a file with all fortune 2000 companies, agencies and other important companies for boosting importance
#org_list = [' '+line.strip()+' ' for line in open("org_list.txt", 'r')]
#for prod, uncomment the next line
#org_list = [' '+line.strip()+' ' for line in open("/var/www/HackDay/org_list.txt", 'r')]


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def make_dicts(cursor, row):
    return dict((cur.description[idx][0], value)
                for idx, value in enumerate(row))

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# Instantiate Authomatic.
authomatic = Authomatic(CONFIG, 'your secret string', report_errors=False)



@app.route('/')
def writers():
    
    
    str_query = 'select * from writers'
    print str_query
    writers = query_db(str_query)
    return render_template('writers.html', writers=writers)



@app.route('/writer/<writer_id>/')
def writer(writer_id):

    article_result = []
    articles = []
    query_str = 'select * from writers where writer_id = \'' + writer_id + '\''
    writer_result = query_db(query_str)

    articles.append(writer_result[0][11])
    articles.append(writer_result[0][21])
    articles.append(writer_result[0][22])
    articles.append(writer_result[0][23])
    articles.append(writer_result[0][24])
    articles.append(writer_result[0][25])



    print articles[0]

    #articles = ['http://venturebeat.com/2015/04/07/an-open-challenge-to-the-digital-video-industry-adopt-tvs-business-model/','https://insights.newscred.com/industry-roundup-how-googles-new-algorithm-will-affect-your-content-marketing/', 'https://insights.newscred.com/infographic-how-to-maximize-content-marketing-distribution/','https://insights.newscred.com/watson-ibm-content-marketing/','https://insights.newscred.com/the-power-of-visual-storytelling/','https://insights.newscred.com/industry-roundup-lifetimes-shoppable-tv-series-modcloths-programmatic-catalogs-just-in-time-marketing/']
    for article in articles:
        if str(article):
            embedly_url = 'https://api.embed.ly/1/oembed?key=21ef9ba1f65e44cf8efd908f7820ca6b&url=' + str(article)
            print embedly_url
            response = urllib2.urlopen(embedly_url)
            article_result.append(json.loads(response.read()))

    return render_template('writer.html', writer_result=writer_result, article_result=article_result)

@app.route('/<profile>/updatepeople/')
def updatePeopleDB(profile, methods=['GET', 'POST']):

    #first get a list of recent people from Twitter
    response = make_response()
    result = authomatic.login(WerkzeugAdapter(request, response), 'tw')
    query_profile = profile
    if profile == ('Percolate' or 'percolate'):
        query_profile = '%40percolate OR percolate.com'
    print result

    if result:
        if result.user:
            # We need to update the user to get more info.
            serialized_credentials = result.user.credentials.serialize()
            session['credentials']= serialized_credentials
            print 'Here are the credss:' + session['credentials']
            result.user.update()
        print 'About to make Twitter call with: ' + session['credentials']
        response = authomatic.access(session['credentials'], url='https://api.twitter.com/1.1/search/tweets.json?q=' + str(query_profile) +'&count=100&result_type=recent')     
         #now take all the people and add them to the people database if needed
        addpeople(response, profile)
        #addperson(['fullname', 'shafqatislam', 'klout_score'])

        #now update everyone's importance values in case anything has changed (like new list of orgs, new keywords for title etc)
        updateimportance(profile)
        recent_people = query_db('select * from people where last_seen like \'%' + time.strftime("%d %b %Y", time.gmtime()) + '%\' and profile = \'' + profile + '\' order by importance desc')
        return render_template('people.html', recent_people=recent_people)

   

    return response

    
def addpeople(tw_response, profile, methods=['GET', 'POST']):
    tw_reponse = tw_response

    #loop through all the twitter handles, check if each person exists, if so update time, if not, add person after getting Full Contact info
    if tw_response.data:
        for item in tw_response.data['statuses']:
            twitter_handle = item['user']['screen_name']
            followers_count = item['user']['followers_count']
            tweet_id = item['id']
            tweet_text = item['text']

            addperson(twitter_handle, followers_count, tweet_id, tweet_text, profile)
        

def getFullContactInfo(handle):

    twitter_handle = handle
    req = urllib2.urlopen('https://api.fullcontact.com/v2/person.json?twitter=' + twitter_handle + '&apiKey=614382520df789e6')
    fc_response = json.loads(req.read())
    organization = ''
    title = ''
    klout_score = 0
    thumbnail_url = ''
    full_name = ''

    if fc_response:
        try:
            fc_response['digitalFootprint']
            klout_score = fc_response['digitalFootprint']['scores'][0]['value']
        except KeyError:
            klout_score = 0

        try:
            thumbnail_url = fc_response['photos'][0]['url']
        except KeyError:
            print 'No Thumbnail Found'

        try:
            for org in fc_response['organizations']:
                if org['current']==True:
                    organization = str(org['name'].encode('utf-8'))
                    title = str(org['title'].encode('utf-8'))
                    print 'found current org'
                    print organization, title
        except KeyError:
            #no organization found so put in LI bio into title field instead
            try:
                for profile in fc_response['socialProfiles']:
                    if profile['type']=="linkedin":
                        organization = ''
                        title = str(profile['bio'].encode('utf-8'))
                        print 'found LI bio'
                        print organization, title

            except KeyError:
                organization = ''
                title = ''
                print organization, title

        try:
            full_name = fc_response['contactInfo']['fullName']
        except KeyError:
            full_name = ''

        return([full_name, twitter_handle, klout_score, organization, title, thumbnail_url])
    else:
        return (None)




def addperson(handle, followers_count, tweet_id, tweet_text, profile):

    #clean up the tweet text for weird characters
    tweet_text = tweet_text.encode('ascii','ignore')
    tweet_text = tweet_text.replace('\'','\'\'')


    content_check = query_db('select * from content where tweet_id = \'' + str(tweet_id) + '\' and twitter_id = \'' + str(handle) + '\' and profile = \'' + profile + '\'')
    if not content_check:
        #this content item  (tweet and profile) has not been seen before so add to content journey and create a new person if needed

        people = query_db('select * from people where twitter_id = \'' + handle + '\' and profile = \'' + profile + '\'')
        if people:
            print 'existing person'
            for person in people:
                #person exists, so just update twitter_followers, engagement and last seen time
                
                #try:
                db = get_db()
                querystr = 'update people set last_tweet = \'' + tweet_text + '\', engagement_count = (engagement_count+1), twitter_followers = \'' + str(followers_count) + '\', last_seen = \'' +  time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()) + '\' where twitter_id = \'' + handle + '\''
                print querystr
                db.execute(querystr)
                db.commit()
                #except:
                    #print 'something went wrong while trying to update a person record for ' + handle
                    #print 'The error was: ' + str(sys.exc_info()[0])


                try:
                    #add an entry to the content journey
                    
                    querystr = 'insert into content (twitter_id, tweet_id, profile, date, tweet_text) values (\'' +  str(handle) + '\',\'' +  str(tweet_id) + '\',\'' + profile + '\',\'' + time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()) + '\',\'' + tweet_text + '\')'
                  
                    print querystr
                    db.execute(querystr)
                    db.commit()
                except:
                    print 'something went wrong while trying to create a content record for an existing person ' + handle
                    print 'The error was: ' + str(sys.exc_info()[0])

        else:
            print 'new person so getting fullcontact info for handle:' + handle
            #first get fullcontact info
            fc_response = getFullContactInfo(handle)
            #create new person
            try:
                db = get_db()
                name = fc_response[0].encode('ascii','ignore')
                name = name.replace('\'','\'\'')

                if followers_count == 0:
                    #without this the log function fails
                    followers_count = 1
                importance = math.log10(float(followers_count)) * fc_response[2]

                querystr = 'insert into people (name, twitter_id, klout_score, first_seen, last_seen, organization, title, thumbnail_url, twitter_followers, engagement_count, profile, last_tweet, importance) values (\'' + name + '\',\'' +  str(handle) + '\',\'' +  str(fc_response[2]) + '\',\'' + time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()) + '\',\'' + time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()) + '\',\'' + str(fc_response[3]) + '\',\'' +  str(fc_response[4]) + '\',\'' +  str(fc_response[5]) + '\',\'' + str(followers_count) + '\',1,\'' + str(profile) + '\',\'' + tweet_text + '\',\'' + str(importance) + '\')'
                print querystr
                db.execute(querystr)
                db.commit()
                try:
                    #add an entry to the content journey
                    querystr = 'insert into content (twitter_id, tweet_id, profile, date, tweet_text) values (\'' +  str(handle) + '\',\'' +  str(tweet_id) + '\',\'' + profile + '\',\'' + time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()) + '\',\'' + tweet_text + '\')'
                    print querystr
                    db.execute(querystr)
                    db.commit()
                except:
                    print 'something went wrong while trying to create a content record for a new person' + handle
                    print 'The error was: ' + str(sys.exc_info()[0])

            except:
                print 'something went wrong while trying to create a person record for ' + handle
                print 'The error was: ' + str(sys.exc_info()[0])



    else:
        print 'Seen this before: ' + str(tweet_id)


@app.route('/<profile>/updateimportance/')
def updateimportance(profile):


    all_people = query_db('select * from people where profile = \'' + profile + '\' order by importance desc')

    if all_people:
        db = get_db()
        for person in all_people:
            handle = person[3]
            twitter_followers = str(person[9])
            title = str(person[10].encode('utf-8'))
            organization = str(person[11].encode('utf-8'))
            boost = 0

            if twitter_followers == '0':
                #without this the log function fails
                twitter_followers = 1
            importance = math.log10(float(twitter_followers)) * person[6]


            #print org_list
            title_list = ['marketing', 'content', 'head', 'president', 'VP', 'vice president', 'brand', 'digital media', 'managing director', 'CEO', 'Chief Executive Officer', 'CMO', 'manager']
            if any(substring.lower() in title.lower() for substring in title_list):
                boost = 100
            
            super_title_list = ['content']
            if any(substring.lower() in title.lower() for substring in title_list):
                boost = 200


            if organization <> "":
                for substring in org_list:
                    if ' ' + organization.lower() + ' ' in substring.lower(): 
                        boost = boost + 200
                        print '1. found a match:' + organization.lower() + ' appeared in ' + substring.lower()
                        break
                    else:
                        if substring.lower() in ' ' + organization.lower() + ' ': 
                            boost = boost + 200
                            print '2. found a match:' + substring.lower() + ' appeared in ' + organization.lower()
                            break


            importance = importance + boost
            #print handle + '-' + str(importance)
           
            db.execute('update people set importance = ' + str(importance) + ' where twitter_id = \'' + handle + '\'')
            db.commit()



#This is not used normally. It is for manually kickick off a process to get twitter follower counts for anyone that failed before or was missing
@app.route('/<profile>/updatefollowers/')
def updatefollowers(profile, methods=['GET', 'POST']):

    #get all the people we want to inspect
    all_people = query_db('select * from people where profile = \'' + profile + '\' and (twitter_followers = 0 or twitter_followers = 1) order by klout_score desc')

    #first get a list of recent people from Twitter
    response = make_response()
    result = authomatic.login(WerkzeugAdapter(request, response), 'tw')
    
    if result:
        if result.user:
            # We need to update the user to get more info.
            serialized_credentials = result.user.credentials.serialize()
            session['credentials']= serialized_credentials
            print 'Here are the credss:' + session['credentials']
            result.user.update()
        
        if all_people:
            db = get_db()
            for person in all_people:
                handle = person[3]
                twitter_followers = person[9]
                if twitter_followers <=1 :
                    #update the follower count for this user
                    print 'About to make Twitter call to get update follower count for ' + handle
                    tw_response = authomatic.access(session['credentials'], url='https://api.twitter.com/1.1/users/lookup.json?screen_name=' + handle)     
                    if tw_response.data:
                        twitter_followers = tw_response.data[0]['followers_count']
                        print twitter_followers                    
                    db.execute('update people set twitter_followers = ' + str(twitter_followers) + ' where twitter_id = \'' + handle + '\'')
                    db.commit()
             #now take all the people and add them to the people database if needed

        return render_template('people.html', all_people=all_people)

    return response

@app.route('/sov/api/v1.0/sov_calc', methods=['GET'])
def sov_calc():

    competitors = request.args.get('competitors')
    topics = request.args.get('topics')

    sov_calc = [
    {
        'percentage': 0.50,
        'competitor': u'NewsCred',
    },
    {
        'percentage': 0.25,
        'competitor': u'Percolate',
    },
    {
        'percentage': 0.10,
        'competitor': u'Contently',
    },
    {
        'percentage': 0.05,
        'competitor': u'Kapost',
    }]

    return jsonify({'sov_calc': sov_calc})

#EVERYTHING BELOW IS FOR THE SOCIAL LISTENING APP

@app.route('/listening/')
def listening():
    """
    Home handler
    """
    return render_template('index.html')

@app.route('/listening/login/<provider_name>/', methods=['GET', 'POST'])
def login_sov(provider_name):
    """
    Login handler, must accept both GET and POST to be able to use OpenID.
    """

    if 'searchterm1' in request.form:
        searchterm1 = request.form['searchterm1']
        session['searchterm1'] = searchterm1
    if 'searchterm2' in request.form:
        searchterm2 = request.form['searchterm2']
        session['searchterm2'] = searchterm2
    if 'searchterm3' in request.form:
        searchterm3 = request.form['searchterm3']
        session['searchterm3'] = searchterm3

    # We need response object for the WerkzeugAdapter.
    response = make_response()
    

    try :
        if len(session['credentials']) > 0:
            loggedin = True
    except KeyError:
            loggedin = False

    if loggedin == True:        
        print 'we already have creds' + session['credentials']
        result = authomatic.login(WerkzeugAdapter(request, response), provider_name)
        if result:
            if result.user:
                # We need to update the user to get more info.
                serialized_credentials = result.user.credentials.serialize()
                session['credentials']= serialized_credentials
                print 'Here are the credss:' + session['credentials']
                result.user.update()
            print 'About to make Twitter call with: ' + session['credentials']
        response1 = authomatic.access(session['credentials'], url='https://api.twitter.com/1.1/search/tweets.json?q=' + urllib.quote_plus(session['searchterm1']))
        response2 = authomatic.access(session['credentials'], url='https://api.twitter.com/1.1/search/tweets.json?q=' + urllib.quote_plus(session['searchterm2']))
        response3 = authomatic.access(session['credentials'], url='https://api.twitter.com/1.1/search/tweets.json?q=' + urllib.quote_plus(session['searchterm3']))
        return render_template('login.html', search1=session['searchterm1'],search2=session['searchterm2'],search3=session['searchterm3'], response1=response1,response2=response2,response3=response3)
                    
    else:
        result = authomatic.login(WerkzeugAdapter(request, response), provider_name)
        if result:
            if result.user:
                # We need to update the user to get more info.
                serialized_credentials = result.user.credentials.serialize()
                session['credentials']= serialized_credentials
                print 'Here are the credss:' + session['credentials']
                result.user.update()
            print 'About to make Twitter call with: ' + session['credentials']
            response1 = authomatic.access(session['credentials'], url='https://api.twitter.com/1.1/search/tweets.json?q=' + urllib.quote_plus(session['searchterm1']))
            response2 = authomatic.access(session['credentials'], url='https://api.twitter.com/1.1/search/tweets.json?q=' + urllib.quote_plus(session['searchterm2']))
            response3 = authomatic.access(session['credentials'], url='https://api.twitter.com/1.1/search/tweets.json?q=' + urllib.quote_plus(session['searchterm3']))
            return render_template('login.html', search1=session['searchterm1'],search2=session['searchterm2'],search3=session['searchterm3'], response1=response1,response2=response2,response3=response3)
                    
    # Don't forget to return the response.
    return response


# Run the app.
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
