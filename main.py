# -*- coding: utf-8 -*-
"""
This is a simple Flask app that uses Authomatic to log users in with Facebook Twitter and OpenID.
"""

from flask import Flask, render_template, request, make_response, session, jsonify, g
import urllib
import sqlite3
import urllib, urllib2
import json

from config import CONFIG

app = Flask(__name__)

app.secret_key = 'Pootchie'
DATABASE = 'newsroom.db'
#for prod uncomment next line
#DATABASE = '/var/www/HackDay/newsroom.db'


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
    if args:
        get_db().commit()
        rv = cur.lastrowid
    else:
        get_db().commit()
        rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv



@app.route('/', methods=['GET', 'POST'])
def list():
    
    search_query = request.args.get('search_query')
    locations = request.args.getlist('location')
    cities = request.args.getlist('cities')
    tiers = request.args.getlist('tier')
    expertise = request.args.getlist('expertise')
    formats = request.args.getlist('format')

    formdetails = locations + tiers + expertise + cities + formats


    if request.query_string:
        str_query = 'select * from writers'
        where = False

    else:
        str_query = 'select * from writers where writing_samples_1 <> \"\"'
        where = True

    
    if search_query:
        if search_query == "":
            str_query = 'select * from writers'
        else:
            where = True
            str_query = 'select * from writers where name like  \'%' + search_query + '%' + '\' or bio like \'%' + search_query + '%' + '\' or area_of_expertise_1 like \'%' + search_query + '%' + '\' or area_of_expertise_2 like \'%' + search_query + '%' + '\' or area_of_expertise_3 like \'%' + search_query + '%' + '\'' 

    if locations:   
        if where == True:
            str_query = str_query + " and (country like "
        else:
            str_query = str_query + " where (country like "
            where = True

        for location in locations:
            str_query = str_query + '\'%' + location + '%\'' + ' OR country like '

        str_query = str_query + '\'%' + locations[0] + '%\')'

    if cities:   
        if where == True:
            str_query = str_query + " and (city like "
        else:
            str_query = str_query + " where (city like "
            where = True

        for city in cities:
            str_query = str_query + '\'%' + city + '%\'' + ' OR city like '

        str_query = str_query + '\'%' + cities[0] + '%\')'



    if tiers:   
        if where == True:
            str_query = str_query + " and (tier like "
        else:
            str_query = str_query + " where (tier like "
            where = True

        for tier in tiers:
            str_query = str_query + '\'%' + tier + '%\'' + ' OR tier like '

        str_query = str_query + '\'%' + tiers[0] + '%\')'

    if formats:   
        if where == True:
            str_query = str_query + " and (style_highlights like "
        else:
            str_query = str_query + " where (style_highlights like "
            where = True

        for format in formats:
            str_query = str_query + '\'%' + format + '%\'' + ' OR tier like '

        str_query = str_query + '\'%' + formats[0] + '%\')'

    if expertise:   
        if where == True:
            str_query = str_query + " and (area_of_expertise_1 like "
        else:
            str_query = str_query + " where (area_of_expertise_1 like "
            where = True

        for expert in expertise:
            str_query = str_query + '\'%' + expert + '%\'' + ' OR area_of_expertise_2 like' + '\'%' + expert + '%\'' + ' or area_of_expertise_3 like' + '\'%' + expert + '%\'' + ' OR area_of_expertise_1 like '

        str_query = str_query + '\'%' + expertise[0] + '%\')'
        print str_query



    print str_query

    writers = query_db(str_query)
    return render_template('list.html', writers=writers, formdetails = formdetails)



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
            try:
                embedly_url = 'https://api.embed.ly/1/oembed?key=21ef9ba1f65e44cf8efd908f7820ca6b&url=' + str(article)
                print embedly_url
                response = urllib2.urlopen(embedly_url)
                article_result.append(json.loads(response.read()))
            except:
                print 'Embedly url failed'
            
            

    return render_template('writer.html', writer_result=writer_result, article_result=article_result)


@app.route('/submit_changes/<writer_id>/', methods=['GET', 'POST'])
def submit_changes(writer_id):
    
    query_str = 'update writers set name = ?, rating = ?, notes = ?, portfolio_link = ?, testimonials = ?, style_highlights = ?, brands = ?, payment_rate = ?, profile_pic = ?, bio = ?, tier = ?, city = ?, country = ?, where_pubished = ?, contact = ?, area_of_expertise_1 = ?, area_of_expertise_2 = ?, area_of_expertise_3 = ?, writing_samples_1 = ?, writing_samples_2 = ?, writing_samples_3 = ?, writing_samples_4 = ?, writing_samples_5 = ? , writing_samples_6 = ? where writer_id = ?'
    
    writer_result = query_db(query_str, (request.args.get('writer_name'), request.args.get('writer_rating'), request.args.get('writer_notes'), request.args.get('writer_portfolio'), request.args.get('writer_testimonials'), request.args.get('writer_style'), request.args.get('writer_brands'), request.args.get('writer_rate'), request.args.get('writer_image'), request.args.get('writer_bio'),request.args.get('writer_tier'), request.args.get('writer_city'), request.args.get('writer_country'), request.args.get('writer_published'), request.args.get('writer_contact'), request.args.get('writer_tag1'), request.args.get('writer_tag2'),request.args.get('writer_tag3'), request.args.get('writer_sample1'),request.args.get('writer_sample2'),request.args.get('writer_sample3'),request.args.get('writer_sample4'),request.args.get('writer_sample5'), request.args.get('writer_sample6'),writer_id))            
    
    return writer(writer_id)



@app.route('/submit_new/', methods=['GET', 'POST'])
def submit_new():

    query_str = 'insert into writers (name, rating, notes, portfolio_link, testimonials, style_highlights, brands, payment_rate, profile_pic,bio,tier,city,country,where_pubished,contact,area_of_expertise_1,area_of_expertise_2,area_of_expertise_3,writing_samples_1,writing_samples_2,writing_samples_3,writing_samples_4,writing_samples_5,writing_samples_6) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
    
    args = (request.args.get('writer_name'), request.args.get('writer_rating'), request.args.get('writer_notes'), request.args.get('writer_portfolio'), request.args.get('writer_testimonials'), request.args.get('writer_style'), request.args.get('writer_brands'), request.args.get('writer_payment'), request.args.get('writer_image'), request.args.get('writer_bio'),request.args.get('writer_tier'), request.args.get('writer_city'), request.args.get('writer_country'), request.args.get('writer_published'), request.args.get('writer_contact'), request.args.get('writer_tag1'), request.args.get('writer_tag2'),request.args.get('writer_tag3'), request.args.get('writer_sample1'),request.args.get('writer_sample2'),request.args.get('writer_sample3'),request.args.get('writer_sample4'),request.args.get('writer_sample5'), request.args.get('writer_sample6'))

    writer_id = query_db(query_str, args)    

    return writer(str(writer_id))


@app.route('/writer/edit/<writer_id>/')
def writer_edit(writer_id):


    query_str = 'select * from writers where writer_id = \'' + writer_id + '\''
    writer_result = query_db(query_str)
    
    return render_template('writer_edit.html', writer_result=writer_result)

@app.route('/writer/delete/<writer_id>/')
def writer_delete(writer_id):


    query_str = 'delete from writers where writer_id = \'' + writer_id + '\''
    writer_result = query_db(query_str)
    
    return list()

@app.route('/writer/create/')
def writer_create():

    return render_template('writer_create.html')



# Run the app.
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
