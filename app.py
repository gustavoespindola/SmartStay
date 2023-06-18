import os

import streamlit as st
import pandas as pd
import plost
import requests
import json
import time
import openai

########################################
# ENV
########################################
os.environ["APIFY_API_TOKEN"] = "apify_api_Ygb8tR6046HXdtJKODl0ADgjoSREGw2aTUK5"

global openai_apikey
global openai_organizationid

########################################
# Functions
########################################

def getReviews(url, maxReviewsPerHotel):
	if url is None or maxReviewsPerHotel is None:
		return 'Please input url and maxReviewsPerHotel'

	url = url.split('?')[0]
	functionUrl = "https://api.apify.com/v2/acts/voyager~booking-reviews-scraper/run-sync-get-dataset-items?token=apify_api_Ygb8tR6046HXdtJKODl0ADgjoSREGw2aTUK5"
	maxReviewsPerHotel = int(maxReviewsPerHotel)
	body = {
		"maxReviewsPerHotel": maxReviewsPerHotel,
		"timeout": 300,
		"proxyConfiguration": {
			"useApifyProxy": True,
			"apifyProxyCountry": "US"
		},
		"startUrls": [{"url": f"{url}"}]
	}

	headers = {
		'Content-Type': 'application/json',
		'Accept': 'application/json'
	}

	response = requests.post(functionUrl, data=json.dumps(body), headers=headers)
	response = response.json()
	return response

def createAnalysis(data):
	print('Creating Analysis')
	df = pd.DataFrame(data)
	with st.spinner('Wait for it...'):
		time.sleep(5)
	# Data cleaning
	avg_rating = df['rating']
	avg_rating = avg_rating.astype(float)
	avg_rating = avg_rating.mean()
	avg_rating = round(avg_rating, 1)

	# This code groups the dataframe by the rating column and counts the number of times each rating appears.
	group = df.groupby('rating').count().reset_index()

	col1, col2 = st.columns(2)
	with col1:
		col1.metric("Average", avg_rating)

	with col2:
		plost.bar_chart(
			data=group,
			bar='id',
			value='rating',
			title='Rating distribution',
		)

	# get reviewTextParts liked
	reviewTextParts = df['reviewTextParts'].apply(pd.Series)
	reviewTextParts = reviewTextParts.reset_index(drop=True)

	reviewLiked = reviewTextParts['Liked']
	reviewDisliked = reviewTextParts['Disliked']

	reviewTitle = df[['reviewTitle']]
	reviewRating = df[['rating']]

	table = pd.concat([reviewRating, reviewTitle, reviewLiked, reviewDisliked], axis=1)

	# call openai
	st.markdown('### ✨ AI Analysis')

	openai.api_key=openai_apikey
	openai.organization=openai_organizationid

	promp = 'Base in DATA Write a Summary paragraph ONLY with the bad Disliked issues about the hotel.\nFinaly write answer the question ¿Do you recommend me to stay at the hotel?? Yes 👍 or not 👎 and why, use an emoji."\nWrite the response using Markdown.'

	response = ''

	responseAi = openai.ChatCompletion.create(
		model="gpt-3.5-turbo-16k",
		user="org-rutlK1tvhpPs5cuj85GbEjoV",
		temperature=0.2,
		max_tokens=256,
		stream=True,
		messages=[
				{"role": "system", "content": f"{promp}\n####DATA:Average rating\t{avg_rating}\n{table}\n####RESPONSE:"},
		]
	)

	# response = 'De los comentarios de los huéspedes, se puede observar que algunos no estuvieron satisfechos con el hecho de tener que pagar una tarifa adicional por el suministro de agua, la limpieza del baño y la ubicación del hotel. también hubo algunas quejas sobre la calidad del café y la potencia del aire acondicionado en algunas habitaciones. en general, parece que la mayoría de los huéspedes disfrutaron de su estancia en el hotel, pero hubo algunos problemas menores que afectaron la experiencia de algunos. en respuesta a la pregunta, sí recomendaría contratar el hotel, pero es importante tener en cuenta las posibles limitaciones mencionadas en los comentarios.'
	
	placeholder = st.empty()

	for message in responseAi:
		data = json.dumps(message['choices'][0])
		if json.loads(data).get('finish_reason') == 'stop':
			break
		message_text = json.loads(data).get('delta').get('content', None)
		if message_text != None:
			response += message_text
			# update text area
			print(response)
			with placeholder.container():
				st.markdown(f'##### {response}')

	st.markdown('### 📊 I have based my analysis on the following data')
	st.dataframe(table)

########################################
# UI
########################################

st.title('SmartStay')
st.subheader('Booking Reviews AI Analysis. AI-Powered Recommendation System for Booking.com Hotels')

# streamlit input url

startFunction = False

with st.sidebar:
	# Settings
	st.markdown('## Settings')
	url = st.text_input('Bookin URL', placeholder='https://www.booking.com/hotel/id/triple-8-suites.es.html')
	openai_apikey = st.text_input('OpenAI API Key', placeholder='sk-**************')
	openai_organizationid = st.text_input('OpenAI Organization ID', placeholder='org-**************')

	# streamlit input maxReviewsPerHotel
	maxReviewsPerHotel = st.number_input('Max Reviews Per Hotel' ,min_value=1, max_value=30, step=1)

	# start function when button clicked
	if st.button('Get Reviews'):
		st.write('Start Function')
		# call function
		# bookingReviews = getReviews(url, maxReviewsPerHotel)
		# bookingReviews
		startFunction = True
	else:
		st.write('')
		startFunction = False

if startFunction:
	reviews = getReviews(url, maxReviewsPerHotel)
	createAnalysis(reviews)
