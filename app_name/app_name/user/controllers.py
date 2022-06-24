from flask import Blueprint, jsonify, request, make_response, render_template
from flask import current_app as app
# from regex import D
from flask_jwt_extended import get_jwt, jwt_required
from flask_cors import cross_origin
from werkzeug.utils import secure_filename
from werkzeug.datastructures import ImmutableMultiDict
from time import gmtime, strftime
import hashlib
import datetime
import requests
import cv2
import os
import numpy as np
import base64
import random
import json
import warnings
import string

from . models import Data

#11 superadmin, 21 Customer
role_group_super_admin = ["11"]
role_group_customer = ["21"] 
role_group_all = ["11", "21"]

#now = datetime.datetime.now()

user = Blueprint('user', __name__, static_folder = '../../upload/foto_user', static_url_path="/media")

#region ================================= FUNGSI-FUNGSI AREA ==========================================================================

def tambahLogs(logs):
	f = open(app.config['LOGS'] + "/" + secure_filename(strftime("%Y-%m-%d"))+ ".txt", "a")
	f.write(logs)
	f.close()

def save(encoded_data, filename):
	arr = np.fromstring(base64.b64decode(encoded_data), np.uint8)
	img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
	return cv2.imwrite(filename, img)

def permission_failed():
    return make_response(jsonify({'error': 'Permission Failed','status_code':403}), 403)

def request_failed():
	return make_response(jsonify({'error': 'Request Failed','status_code':403}), 403)

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

def randomString(stringLength):
	"""Generate a random string of fixed length """
	letters = string.ascii_lowercase
	return ''.join(random.choice(letters) for i in range(stringLength))

def random_string_number_only(stringLength):
	letters = string.digits
	return ''.join(random.choice(letters) for i in range(stringLength))

#endregion ================================= FUNGSI-FUNGSI AREA ===============================================================


#region ================================= MY PROFILE AREA ==========================================================================

#endregion ================================= MY PROFILE AREA ==========================================================================


#region ================================= CUSTOMER AREA ==========================================================================


#endregion ================================= CUSTOMER AREA ==========================================================================


#region ================================= USER AREA ==========================================================================

@user.route('/reset_password', methods=['POST', 'OPTIONS'])
@cross_origin()
def reset_password():
	ROUTE_NAME = str(request.path)
	try:
		data = request.json
		if "email" not in data:
			return parameter_error("Missing email in Request Body")
		email = data["email"] 

		# Check if email is exist and active
		dt = Data()
		query_temp = "SELECT id_user, email, nama, status_user FROM user WHERE email = %s AND is_delete != 1 "
		values_temp = (email,)
		data_email = dt.get_data(query_temp, values_temp)
		if len(data_email) == 0:
			return defined_error("Email belum terdaftar")
		if str(data_email[0]["status_user"]) != "11":
			return defined_error("Akun tidak aktif atau terblokir")

		nama = data_email[0]["nama"]

		newpass 		= randomString(12)	
		newpass_encoded = hashlib.md5(newpass.encode('utf-8')).hexdigest()

		# Try send email first then change password in database
		try:
			template = render_template('reset_password.html', nama=nama, password=newpass)
			url = app.config['BISAAI_MAIL_SERVER']
			payload = json.dumps(
				{
					'pengirim': app.config['BISAAI_MAIL_SENDER'],
					'penerima': email,
					'isi': template,
					'judul': '[Reset Password Bisa Network]'
				})
			files = {}
			headers = {
				'X-API-KEY': app.config['BISAAI_MAIL_API_KEY'],
				'Content-Type': 'application/json'
			}
			response = requests.request('POST', url, headers = headers, data = payload, files = files, allow_redirects=False, verify=False)
			if response.status_code != 200:
				raise Exception()
		except Exception as e:
			return defined_error("Reset Password Gagal")

		# If send email success, change password in database
		query = "UPDATE user SET password = %s WHERE email = %s"
		values = (newpass_encoded, email)
		dt.insert_data(query, values)
		#======================================================================

		try:
			logs = secure_filename(strftime("%Y-%m-%d %H:%M:%S"))+" - "+ROUTE_NAME+" - id_user = "+str(id_user)+" - roles = "+str(role)+" - email = "+email+"\n"
		except Exception as e:
			logs = secure_filename(strftime("%Y-%m-%d %H:%M:%S"))+" - "+ROUTE_NAME+" - id_user = NULL - roles = NULL - email = "+email+"\n"
		tambahLogs(logs)

		hasil = 'Berhasil Reset Password'
		return make_response(jsonify({'status_code':200 , 'description': hasil} ), 200)
	except Exception as e:
		return bad_request(str(e))

@user.route('/insert_mahasiswa', methods = ['POST'])
def insert_mahasiswa():
	ROUTE_NAME = str(request.path)
	now = datetime.datetime.now()
	try:
		dt =  Data()
		data =  request.json
		if "password" not in data:
			return parameter_error("Missing password in request body")
		if "email" not in data:
			return parameter_error("Missing email in request body")
		if "nama" not in data:
			return parameter_error("Missing nama in request body")
		if "nim" not in data:
			return parameter_error("Missing nim in request body")
		if "jurusan" not in data:
			return parameter_error("Missing jurusan in request body")
		if "angkatan" not in data:
			return parameter_error("Missing angkatan in request body")
		
		password  =  data['password']
		email  =  str(data['email'])
		nama =  data['nama']
		nim =  str(data['nim'])
		jurusan =  data['jurusan']
		angkatan = data['angkatan']
		
		cek_email  =  is_unique('user',email,'email')
		if cek_email != True:
			return parameter_error('email telah terdaftar')
		cek_nim =  is_unique('mahasiswa',nim,'nim')
		if cek_nim != True :
			return parameter_error('nim telah terdaftar')
		enc_password  =  hashlib.md5(password.encode('utf-8')).hexdigest()
		query =  "INSERT INTO user (nama,email,password,role) VALUES (%s,%s,%s,%s) "
		values = (nama,email,enc_password,2)
		dt.insert_data(query,values)
		# return('berhasil')
		query_temp =  'SELECT id_user FROM user WHERE nama=%s AND email=%s'
		value_temp = (nama,email)
		hasil  =  dt.get_data(query_temp,value_temp)
		if len(hasil)!=1:
			return parameter_error('Email/Nama is Duplicated')
		id_user = hasil[0]['id_user']
		query2 = "INSERT INTO mahasiswa (nim,id_user,jurusan,angkatan) VALUES(%s,%s,%s,%s)"
		# return nim
		values2 =  (nim,id_user,jurusan,angkatan)
		dt.insert_data(query2,values2)
		return ('Pendaftaran berhasil')
	except Exception as e:
		return bad_request(str(e))

@user.route('/insert_dosen', methods = ['POST'])
def insert_dosen():
	ROUTE_NAME = str(request.path)
	now = datetime.datetime.now()
	try:
		dt =  Data()
		data =  request.json
		if "password" not in data:
			return parameter_error("Missing password in request body")
		if "email" not in data:
			return parameter_error("Missing email in request body")
		if "nama" not in data:
			return parameter_error("Missing nama in request body")
		if "nip" not in data:
			return parameter_error("Missing nip in request body")
		if "jurusan" not in data:
			return parameter_error("Missing jurusan in request body")

		password  =  data['password']
		email  =  data['email']
		nama =  data['nama']
		nip =  data['nip']
		jurusan =  data['jurusan']
		cek_email  =  is_unique('user',email,'email')
		if cek_email != True:
			return parameter_error('email telah terdaftar')
		cek_nip =  is_unique('dosen',nip,'nip')
		if cek_nip != True :
			return parameter_error('nip telah terdaftar')
		enc_password  =  hashlib.md5(password.encode('utf-8')).hexdigest()
		query =  "INSERT INTO user (nama,email,password,role) VALUES (%s,%s,%s,%s) "
		values = (nama,email,enc_password,1, )
		dt.insert_data(query,values)
		query_temp =  'SELECT id_user FROM user WHERE nama=%s AND email=%s'
		value_temp = (nama,email, )
		hasil  =  dt.get_data(query_temp,value_temp)
		if len(hasil)!=1:
			return parameter_error('Email/Nama is Duplicated')
		id_user = hasil[0]['id_user']
		query2 = "INSERT INTO dosen (nip,id_user,jurusan,status) VALUES(%s,%s,%s,%s)"
		values2 =  (nip,id_user,jurusan,1)
		dt.insert_data(query2,values2)
		return ('Pendaftaran berhasil')
	except Exception as e:
		return bad_request(str(e))
@user.route('/get_mahasiswa',methods=['GET','POST'])
def get_mahasiswa():
    print('hit api')
    dt =  Data()
    # data = request.json
    # print()
    data = request.get_json(force=True)
    print(type(data))
    print(data)
    if 'nim' not in data:
        return jsonify('Missin nim in request body')
    nim =  data['nim']
    query =  "SELECT * FROM mahasiswa LEFT JOIN user ON mahasiswa.id_user = user.id_user WHERE nim=%s"
    values  = (nim,)
    hasil =  dt.get_data(query,values)
    hasil =  hasil[0]
    return jsonify(hasil)

#endregion ================================= USER AREA ==========================================================================
def is_unique(tabel, value, kolom):
	dt = Data()
	query =  "SELECT * FROM "+ tabel +" WHERE "+kolom+"=%s"
	values =  (value,)
	print(query)
	print(values)
	hasil = dt.get_data(query,values)
	# return hasil
	if len(hasil) != 0:
		return False
	else:
		return True