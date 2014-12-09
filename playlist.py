from flask import Flask, render_template, request, redirect
import requests
from textblob import TextBlob
import settings
import random
import json

app = Flask(__name__)

API_KEY = settings.API_KEY
GENRE_JSON = 'list_genres.json'

def genres_to_feels():
	with open(GENRE_JSON) as j:
		g = json.load(j)
	genre_list = g['response']['genres']
	genre_names = [genre_list[x]['name'] for x in range(len(genre_list))]
	blobs = map(TextBlob, genre_names)
	sentiments = {str(blob): blob.sentiment.polarity for blob in blobs}
	return sentiments
	
def simple_sentiment(text):
	'''-1 is :(, 0 is :|, 1 is :) for now'''
	blob = TextBlob(text)
	polarity = blob.sentiment.polarity
	if polarity > .5:
		return 1
	elif 0 < polarity <= .5:
		return 0
	elif polarity <= 0:
		return -1

def sentiment_to_songs(sadness_int, sentiments):
	'''sadness int comes from simple_sentiment,
	sentiments is a dict from genres_to_feels'''
	happyish = [k for k in sentiments if sentiments[k] > 0]
	saddish = [k for k in sentiments if sentiments[k] < 0]
	meh = [k for k in sentiments if sentiments[k] == 0]
	if sadness_int == -1: #:(
		genre = str(random.choice(saddish))
		return genre
	elif sadness_int == 0: #:|
		genre = str(random.choice(meh))
		return genre
	elif sadness_int == 1: #:)
		genre = str(random.choice(happyish))
	return genre

def get_song_ids(feels_words):
	feels_dict = genres_to_feels()
	sadness_int = simple_sentiment(feels_words)
	first_genre = sentiment_to_songs(sadness_int, feels_dict)
	second_genre = sentiment_to_songs(sadness_int, feels_dict)
	third_genre = sentiment_to_songs(sadness_int, feels_dict)
	tracks = requests.get('http://developer.echonest.com/api/v4/playlist/static?api_key=' + API_KEY + '&genre={0}&genre={1}&genre={2}&format=json&bucket=id:spotify&bucket=tracks&limit=true&type=genre-radio'.format(first_genre, second_genre, third_genre)).json()['response']['songs']
	spotify_song_ids = []
	for x in range(len(tracks)):
		spotify_song_ids.append(str(tracks[x]['tracks'][0]['foreign_id'][14:]))
	return spotify_song_ids #list

@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == 'GET':
		return render_template('index.html')
	elif request.method == 'POST': #what to do on refresh...
		user_feels = request.form['feels']
 		user_songs = ','.join(get_song_ids(user_feels))
 		return render_template('index.html', songids=user_songs) 

if __name__ == '__main__':
    app.run(debug=True)
