import flask
import psycopg2
from flask import Flask, request, jsonify, render_template
from tfidf import get_tfidf
import sys  
import hashlib

reload(sys)  
sys.setdefaultencoding('utf8')

app = flask.Flask(__name__)
app.config["DEBUG"] = True

def db_connect(sql):
	connection = psycopg2.connect(user = "", password = "", host = "localhost", port = "5432", database = "")
	connection.autocommit = True
	try:
		cursor = connection.cursor()
		cursor.execute(sql)
		return cursor.fetchall()
	except (Exception, psycopg2.Error) as error :
		print ("Error while connecting to PostgreSQL", error)
	finally:
		cursor.close()
		if(connection):
			connection.close()
			print("PostgreSQL connection is closed")


@app.route('/', methods=['GET'])
def home():
	return render_template('index.html')
	

@app.route('/keyword', methods=['GET','POST'])
def keyword():
	keyword = request.form['keyword']
	db_result = get_tfidf(keyword)
	html = ""
	for row in db_result[0]:
		html += "<tr class='tfidf-tr'><td>" + str(row[0]) + "</td><td>" + str(row[1]) + "</td><td>" + str(row[2] )+ "</td><td>" + str(row[3] )+ "</td><td>" + str(row[4]) + "</td></tr>"

	return render_template('tfidf.html', searchword = keyword, table = html)


@app.route('/login', methods=['GET','POST'])
def login():
	username = request.form['username']
	password = request.form['password']

	result = db_connect("SELECT approved, email, password FROM public.users WHERE email = '" + username + "';")

	if result:
		if result[0][0] == True:
			if result[0][1] == username and result[0][2] == password:
				return render_template('home.html')
			else:
				return render_template('index.html', error='The username and/or password have been entered incorrectly. Please enter your username and password or create an account.')
		else:
			return render_template('index.html', error='Your account needs approval. Please contact your system administrator')
	else:
		return render_template('index.html', error='There are no accounts with that username. Please enter your username and password or create an account.')


	return jsonify(result)


@app.route('/account', methods=['GET','POST'])
def account():
	if request.method == 'POST':
		fName = request.form['fName']
		lName = request.form['lName']
		email = request.form['email']
		password = request.form['password']

		if not fName or not lName or not email or not password:
			return render_template('create.html', error='Please fill out all fields.')
		else:
			db_connect("INSERT INTO public.users (f_name, l_name, approved, email, password, user_role) SELECT '" + fName + "', '" + lName + "', 'False', '" + email + "', '" + password + "', 'user' WHERE NOT EXISTS (SELECT email FROM public.users WHERE email = '" + email + "');")
			# db_connect("INSERT INTO public.users (f_name, l_name, approved, email, passwd, user_role) SELECT '" + fName + "', '" + lName + "', 'False', '" + email + "', '" + password + "', 'user' WHERE NOT EXISTS (SELECT email FROM public.users WHERE email = '" + email + "');")
			return render_template('index.html')


@app.route('/create', methods=['GET','POST'])
def create():
	return render_template('create.html')


@app.route('/api/users', methods=['GET'])
def api_users():
	records = db_connect("SELECT email FROM public.users WHERE approved = 'false';")
	results = [list(i) for i in records]
	return jsonify(results)


@app.route('/api/approve', methods=['GET','PUT'])
def approve_users():
	content = request.get_json()
	check = db_connect("SELECT user_role, password FROM public.users WHERE email = '" + content['user'] + "';")
	if check[0][1] == content['password']:
		if check[0][0] == "admin":
			records = db_connect("UPDATE public.users SET approved = 'true' WHERE email = '" + content['email'] + "';")
			return jsonify(records)
		else:
			return "You do not have access to approve accounts."
	else:
		return "Your username or password is incorrect."


app.run(debug=True)