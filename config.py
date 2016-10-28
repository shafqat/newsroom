# config.py

from authomatic.providers import oauth2, oauth1

CONFIG = {
    
    'tw': { # Your internal provider name
           
        # Provider class
        'class_': oauth1.Twitter,
        'id': 1234,         
        
        # Twitter is an AuthorizationProvider so we need to set several other properties too:
        'consumer_key': 'NqDN6RTFyJeuMa6P8nUFFQ',
        'consumer_secret': '6KWDDW889GczHXaQYRDlerLqOo91ZAF0OLtmypIlGFo',
    },
    
    'fb': {
           
        'class_': oauth2.Facebook,
        
        # Facebook is an AuthorizationProvider too.
        'consumer_key': '########################',
        'consumer_secret': '########################',
        
        # But it is also an OAuth 2.0 provider and it needs scope.
        'scope': ['user_about_me', 'email', 'publish_stream'],
    },
}