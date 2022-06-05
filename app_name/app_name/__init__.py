# -*- coding: utf-8 -*-
import sys
from flask import Flask, jsonify, request, make_response, render_template, redirect
from flask_jwt_extended import create_access_token, get_jwt, jwt_required, JWTManager
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
from time import gmtime, strftime
import json
import datetime
import os
import base64
import random
import hashlib
import warnings

from . data import Data
from . import config as CFG


## IMPORT BLUEPRINT
# from .contoh_blueprint.controllers import contoh_blueprint
from .user.controllers import user
from .lokasi.controllers import lokasi
from .matakuliah.controller import matakuliah
#region >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> CONFIGURATION <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
app = Flask(__name__, static_url_path=None) #panggil modul flask

# CORS Configuration
cors = CORS(app, resources={r"*": {"origins": "*"}})
app.config['CORS_HEADERS']							= 'Content-Type'

# Flask JWT Extended Configuration
app.config['SECRET_KEY'] 							= CFG.JWT_SECRET_KEY
app.config['JWT_HEADER_TYPE']						= CFG.JWT_HEADER_TYPE
app.config['JWT_ACCESS_TOKEN_EXPIRES'] 				= datetime.timedelta(days=1) #1 hari token JWT expired
jwt = JWTManager(app)

# Application Configuration
app.config['PRODUCT_ENVIRONMENT']					= CFG.PRODUCT_ENVIRONMENT
app.config['BACKEND_BASE_URL']						= CFG.BACKEND_BASE_URL


# LOGS FOLDER PATH
app.config['LOGS'] 									= CFG.LOGS_FOLDER_PATH

# UPLOAD FOLDER PATH
UPLOAD_FOLDER_PATH									= CFG.UPLOAD_FOLDER_PATH

# Cek apakah Upload Folder Path sudah diakhiri dengan slash atau belum
if UPLOAD_FOLDER_PATH[-1] != "/":
	UPLOAD_FOLDER_PATH							= UPLOAD_FOLDER_PATH + "/"

app.config['UPLOAD_FOLDER_FOTO_USER'] 				= UPLOAD_FOLDER_PATH+"foto_user/"
app.config['UPLOAD_FOLDER_FOTO_TEMPAT_UJI_KOMPETENSI'] 	= UPLOAD_FOLDER_PATH+"lokasi/foto_tempat_uji_kompetensi/"

#Create folder if doesn't exist
list_folder_to_create = [
	app.config['LOGS'],
	app.config['UPLOAD_FOLDER_FOTO_USER'],
	app.config['UPLOAD_FOLDER_FOTO_TEMPAT_UJI_KOMPETENSI']
]
for x in list_folder_to_create:
	if os.path.exists(x) == False:
		os.makedirs(x)

#endregion >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> CONFIGURATION <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


#region >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> FUNCTION AREA <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

def defined_error(description, error="Defined Error", status_code=499):
	return make_response(jsonify({'description':description,'error': error,'status_code':status_code}), status_code)

def parameter_error(description, error= "Parameter Error", status_code=400):
	if app.config['PRODUCT_ENVIRONMENT'] == "DEV":
		return make_response(jsonify({'description':description,'error': error,'status_code':status_code}), status_code)
	else:
		return make_response(jsonify({'description':"Terjadi Kesalahan Sistem",'error': error,'status_code':status_code}), status_code)

def bad_request(description):
	if app.config['PRODUCT_ENVIRONMENT'] == "DEV":
		return make_response(jsonify({'description':description,'error': 'Bad Request','status_code':400}), 400) #Development
	else:
		return make_response(jsonify({'description':"Terjadi Kesalahan Sistem",'error': 'Bad Request','status_code':400}), 400) #Production

def tambahLogs(logs):
	f = open(app.config['LOGS'] + "/" + secure_filename(strftime("%Y-%m-%d"))+ ".txt", "a")
	f.write(logs)
	f.close()

#endregion >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> FUNCTION AREA <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


#region >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> AUTH AREA (JWT) <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

@app.route("/login_customer", methods=["POST"])
@cross_origin()
def login_customer():
	ROUTE_NAME = request.path

	data = request.json
	if "nim" not in data:
		return parameter_error("Missing nim in Request Body")
	if "password" not in data:
		return parameter_error("Missing password in Request Body")

	nim = data["nim"]
	password = data["password"]
	password_enc = hashlib.md5(password.encode('utf-8')).hexdigest() # Convert password to md5

	# Check credential in database
	dt = Data()
	query =  "SELECT jurusan,nama,nim FROM user rfid WHERE nim=%s"
	values = (nim, )
	data_user =  dt.get_data(query,values)
	return (jsonify(data_user))
	
	if len(data_user) == 0:
		return defined_error("Email not Registered or not Active", "Invalid Credential", 401)
	data_user = data_user[0]
	nim = data_user["nim"]
	db_password = data_user["password"]
	nama =  data_user["nama"]

	if password_enc != db_password:
		return defined_error("Wrong Password", "Invalid Credential", 401)

	role = 21
	role_desc = "mahasiswa"

	jwt_payload = {
		"nim" :nim,
		"nama" : nama,
		"role" : role ,
		"role_desc" : role_desc,
	}

	access_token = create_access_token(nim, additional_claims=jwt_payload)

	# Update waktu terakhir login customer

	return jsonify(access_token=access_token)

@app.route("/login_admin", methods=["POST"])
@cross_origin()
def login_admin():
	ROUTE_NAME = request.path

	data = request.json
	if "username" not in data:
		return parameter_error("Missing username in Request Body")
	if "password" not in data:
		return parameter_error("Missing password in Request Body")

	username = data["username"]
	password = data["password"]

	username = username.lower()
	password_enc = hashlib.md5(password.encode('utf-8')).hexdigest() # Convert password to md5

	# Check credential in database
	dt = Data()
	query = """ SELECT b.id_user, b.email, b.password 
			FROM admin a LEFT JOIN user b ON a.id_user=b.id_user
			WHERE a.is_aktif = 1 AND a.is_delete != 1 AND b.status_user = 11 AND b.is_delete != 1 AND  
			b.email = %s """
	values = (username, )
	data_user = dt.get_data(query, values)
	if len(data_user) == 0:
		return defined_error("Email not Registered or not Active", "Invalid Credential", 401)
	data_user = data_user[0]
	db_id_user = data_user["id_user"]
	db_password = data_user["password"]

	if password_enc != db_password:
		return defined_error("Wrong Password", "Invalid Credential", 401)

	role = 11
	role_desc = "SUPER ADMIN"

	jwt_payload = {
		"id_user" : db_id_user,
		"role" : role,
		"role_desc" : role_desc,
		"email" : username
	}

	access_token = create_access_token(username, additional_claims=jwt_payload)

	try:
		logs = secure_filename(strftime("%Y-%m-%d %H:%M:%S"))+" - "+ROUTE_NAME+" - id_user = "+str(db_id_user)+" - roles = "+str(role)+"\n"
	except Exception as e:
		logs = secure_filename(strftime("%Y-%m-%d %H:%M:%S"))+" - "+ROUTE_NAME+" - id_user = NULL - roles = NULL\n"
	tambahLogs(logs)

	return jsonify(access_token=access_token)

@app.route('/cek_credential', methods=['GET', 'OPTIONS']) 
@jwt_required() #Need JWT Token
@cross_origin()
def cek_credential():
	dt = Data()

	id_user = str(get_jwt()["id_user"])
	role 	= str(get_jwt()["role"])
	
	dt = Data()
	query = "SELECT * FROM user WHERE id_user = %s AND is_delete = 0"
	values = (id_user, )
	hasil = dt.get_user(query, values)
	

	# Get role description
	query_temp = "SELECT role_description FROM static_role_description WHERE id_role = %s"
	values_temp = (role, )
	data_role = dt.get_data(query_temp, values_temp)
	if len(data_role) == 0:
		role_description = "UNDEFINED"
	else:
		role_description = data_role[0]["role_description"]

	# Add role and role_description to json payload
	hasil[0]["role"] = role
	hasil[0]["role_description"] = role_description

	if len(hasil) == 0:
		return defined_error("User Not Found", "Data not found", 404)

	return jsonify(hasil)



@app.route("/halaman_login", methods=["GET"])
def halaman_login():
    return render_template
#endregion >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> AUTH AREA (JWT) <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


#region >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> INDEX ROUTE AREA <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

@app.route("/")
def homeee():
	return "Bisa LSP Backend"

#endregion >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> INDEX ROUTE AREA <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


#region >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ERROR HANDLER AREA <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# fungsi error handle Halaman Tidak Ditemukan
@app.errorhandler(404)
@cross_origin()
def not_found(error):
	return make_response(jsonify({'error': 'Tidak Ditemukan','status_code':404}), 404)

#fungsi error handle Halaman internal server error
@app.errorhandler(500)
@cross_origin()
def not_found(error):
	return make_response(jsonify({'error': 'Error Server','status_code':500}), 500)

#endregion >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ERROR HANDLER AREA <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


#--------------------- REGISTER BLUEPRINT ------------------------

app.register_blueprint(user, url_prefix='/user')
app.register_blueprint(lokasi, url_prefix='/lokasi')
app.register_blueprint(matakuliah, url_prefix='/matakuliah')

#--------------------- END REGISTER BLUEPRINT ------------------------
