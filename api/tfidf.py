from datetime import datetime
from itertools import chain
import sys, os
import psycopg2
import math
import json

totalStudies = 0
totalWords = 0
results = list()
tfidfFinal = list()
chars = ["'","[","@","_","!","#","$","%","^","&","*","(",")","<",">","?","/","|",",","\\","`","~","-",".","=","+","\""]

def computeTF(studies): # This function computes the term frequency of text
	global totalStudies
	global wordsDict
	tfWord = list()
	tfList = list()
	totalStudies = len(studies)
	for study in studies:
		words = study[0].split(" ")
		for word in words:
			global totalWords
			wordOccurances = words.count(word)
			if word.endswith(tuple(chars)):
				word = word[:-1]
			if word.startswith(tuple(chars)):
				word = word[1:]
			tfWord.append(word)
			tfWord.append(round(wordOccurances/float(len(words)), 3))
			tfList.append(tfWord)
			tfWord = list()
			totalWords += 1
	return tfList


def computeTFIDF(tfList): # This function computes the term frequency - inverse document frequency of a collection of text
	wordInDoc = 0
	global studies
	for word in tfList:
		for result in results:
			if word[0] in result[0]:
				wordInDoc += 1
		word.append(round(math.log10(totalStudies / float(wordInDoc)), 3))
		word.append(round((word[1] * word[2]), 3))
		word.append(wordInDoc)
		wordInDoc = 0
	return tfList


def db_connect(keyword): # Provides a connection to the clinical trials database
	global results
	connection = psycopg2.connect(user = "", password = "", host = "aact-db.ctti-clinicaltrials.org", port = "5432", database = "aact")
	try:
		cursor = connection.cursor()
		cursor.execute("SELECT official_title FROM ctgov.studies WHERE official_title LIKE '%" + keyword + "%' LIMIT 100;")
		records = cursor.fetchall()
		results = [list(i) for i in records]
		return results
	except (Exception, psycopg2.Error) as error :
		print ("Error while connecting to PostgreSQL", error)
	finally:
		if(connection):
			cursor.close()
			connection.close()
			print("PostgreSQL connection is closed")


def sortList(tfidf): # This function will sort the list in order of tf-idf score
	global tfidfFinal
	global tfidfSorted
	tfidfSorted = sorted(tfidf,key=lambda x: x[3], reverse=True)
	for word in tfidfSorted:
		check = False
		if not tfidfFinal:
			tfidfFinal.append(word)
		else:
			for keyword in tfidfFinal:
				if word[0] == keyword[0]:
					check = True
			if check == False:
				tfidfFinal.append(word)
	return tfidfFinal


def get_tfidf(keyword): # This function calls all the functions needed to calculate tf-idf for a given keyword
	global totalStudies
	global totalWords
	startTime = datetime.now()
	studies = db_connect(keyword)
	tf = computeTF(studies)
	idf = computeTFIDF(tf)
	tfidfSorted = sortList(idf)
	totalTime = datetime.now() - startTime
	uniqueWords = len(tfidfSorted)

	return [tfidfSorted, str(totalStudies), str(totalWords), str(uniqueWords), str(totalTime)]