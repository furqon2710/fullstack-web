from flask import Blueprint, jsonify, request, make_response, render_template
from flask import current_app as app
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

lokasi = Blueprint('lokasi', __name__, static_folder = '../../upload/lokasi', static_url_path="/media")

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


#region ================================= TEMPAT UJI KOMPETENSI AREA ==========================================================================

@lokasi.route('/get_tempat_uji_kompetensi', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_tempat_uji_kompetensi():
	try:
		ROUTE_NAME = str(request.path)
		
		dt = Data()

		query = """ SELECT a.*, b.id_provinsi, b.nama_kota, c.nama_provinsi
					FROM tempat_uji_kompetensi a
					LEFT JOIN kota b ON a.id_kota=b.id_kota
					LEFT JOIN provinsi c ON b.id_provinsi=c.id_provinsi
					WHERE a.is_delete != 1 """
		values = ()

		page = request.args.get("page")
		id_tempat_uji_kompetensi = request.args.get("id_tempat_uji_kompetensi")
		id_kota = request.args.get("id_kota")
		id_provinsi = request.args.get("id_provinsi")
		search = request.args.get("search")
		is_aktif = request.args.get("is_aktif")
		order_by = request.args.get("order_by")

		if (page == None):
			page = 1
		if id_tempat_uji_kompetensi:
			query += " AND a.id_tempat_uji_kompetensi = %s "
			values += (id_tempat_uji_kompetensi, )
		if id_kota:
			query += " AND a.id_kota = %s "
			values += (id_kota, )
		if id_provinsi:
			query += " AND c.id_provinsi = %s "
			values += (id_provinsi, )
		if search:
			query += """ AND CONCAT_WS("|", a.nama_tempat_uji_kompetensi) LIKE %s """
			values += ("%"+search+"%", )
		if is_aktif:
			query += " AND a.is_aktif = %s "
			values += (is_aktif, )

		if order_by:
			if order_by == "id_asc":
				query += " ORDER BY a.id_tempat_uji_kompetensi ASC "
			elif order_by == "id_desc":
				query += " ORDER BY a.id_tempat_uji_kompetensi DESC "
			else:
				query += " ORDER BY a.id_tempat_uji_kompetensi DESC "
		else:
			query += " ORDER BY a.id_tempat_uji_kompetensi DESC "

		rowCount = dt.row_count(query, values)
		hasil = dt.get_data_lim(query, values, page)
		hasil = {'data': hasil , 'status_code': 200, 'page': page, 'offset': '10', 'row_count': rowCount}
		########## INSERT LOG ##############
		imd = ImmutableMultiDict(request.args)
		imd = imd.to_dict()
		param_logs = "[" + str(imd) + "]"
		try:
			logs = secure_filename(strftime("%Y-%m-%d %H:%M:%S"))+" - "+ROUTE_NAME+" - id_user = "+str(id_user)+" - roles = "+str(role)+" - param_logs = "+param_logs+"\n"
		except Exception as e:
			logs = secure_filename(strftime("%Y-%m-%d %H:%M:%S"))+" - "+ROUTE_NAME+" - id_user = NULL - roles = NULL - param_logs = "+param_logs+"\n"
		tambahLogs(logs)
		####################################
		return make_response(jsonify(hasil),200)
	except Exception as e:
		return bad_request(str(e))

@lokasi.route('/insert_tempat_uji_kompetensi', methods=['POST', 'OPTIONS'])
@jwt_required()
@cross_origin()
def insert_tempat_uji_kompetensi():
	ROUTE_NAME = str(request.path)

	now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)

	id_user = str(get_jwt()["id_user"])
	role = str(get_jwt()["role"])

	if role not in role_group_super_admin:
		return permission_failed()

	try:
		dt = Data()
		data = request.json

		# Check mandatory data
		if "id_kota" not in data:
			return parameter_error("Missing id_kota in Request Body")
		if "nama_tempat_uji_kompetensi" not in data:
			return parameter_error("Missing nama_tempat_uji_kompetensi in Request Body")
		if "deskripsi_tempat_uji_kompetensi" not in data:
			return parameter_error("Missing deskripsi_tempat_uji_kompetensi in Request Body")
		if "alamat" not in data:
			return parameter_error("Missing alamat in Request Body")

		id_kota 						= data["id_kota"]
		nama_tempat_uji_kompetensi 		= data["nama_tempat_uji_kompetensi"]
		deskripsi_tempat_uji_kompetensi = data["deskripsi_tempat_uji_kompetensi"]
		alamat 							= data["alamat"]

		# cek apakah data kota ada
		query_temp = "SELECT id_kota FROM kota WHERE is_delete!=1 AND id_kota = %s"
		values_temp = (id_kota, )
		data_temp = dt.get_data(query_temp, values_temp)
		if len(data_temp) == 0:
			return defined_error("Gagal, Data Kota tidak ditemukan")

		# Cek data-data opsional

		if "nomor_telepon" in data:
			nomor_telepon = data["nomor_telepon"]
		else:
			nomor_telepon = None

		if "email" in data:
			email = data["email"]
		else:
			email = None

		if "longitude" in data:
			longitude = data["longitude"]
		else:
			longitude = None

		if "latitude" in data:
			latitude = data["latitude"]
		else:
			latitude = None

		if "foto_tempat_uji_kompetensi" in data:
			filename_photo = secure_filename(now.strftime("%Y-%m-%d %H:%M:%S")+"_"+str(random_string_number_only(5))+"_foto_tempat_uji_kompetensi.png")
			save(data["foto_tempat_uji_kompetensi"], os.path.join(app.config['UPLOAD_FOLDER_FOTO_TEMPAT_UJI_KOMPETENSI'], filename_photo))

			foto_tempat_uji_kompetensi = filename_photo
		else:
			foto_tempat_uji_kompetensi = None

		# Insert to table tempat uji kompetensi
		query = "INSERT INTO tempat_uji_kompetensi (id_kota, nama_tempat_uji_kompetensi, deskripsi_tempat_uji_kompetensi, alamat, nomor_telepon, email, longitude, latitude, foto_tempat_uji_kompetensi) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
		values = (id_kota, nama_tempat_uji_kompetensi, deskripsi_tempat_uji_kompetensi, alamat, nomor_telepon, email, longitude, latitude, foto_tempat_uji_kompetensi)
		id_tempat_uji_kompetensi = dt.insert_data_last_row(query, values)

		hasil = "Berhasil menambahkan tempat uji kompetensi"
		hasil_data = {
			"id_tempat_uji_kompetensi" : id_tempat_uji_kompetensi
		}
		try:
			logs = secure_filename(strftime("%Y-%m-%d %H:%M:%S"))+" - "+ROUTE_NAME+" - id_user = "+str(id_user)+" - roles = "+str(role)+"\n"
		except Exception as e:
			logs = secure_filename(strftime("%Y-%m-%d %H:%M:%S"))+" - "+ROUTE_NAME+" - id_user = NULL - roles = NULL\n"
		tambahLogs(logs)
		return make_response(jsonify({'status_code':200, 'description': hasil, 'data' : hasil_data} ), 200)
	except Exception as e:
		return bad_request(str(e))

@lokasi.route('/update_tempat_uji_kompetensi', methods=['PUT', 'OPTIONS'])
@jwt_required()
@cross_origin()
def update_tempat_uji_kompetensi():
	ROUTE_NAME = str(request.path)

	now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)

	id_user 		= str(get_jwt()["id_user"])
	role 			= str(get_jwt()["role"])

	if role not in role_group_super_admin:
		return permission_failed()
	
	try:
		dt = Data()
		data = request.json

		if "id_tempat_uji_kompetensi" not in data:
			return parameter_error("Missing id_tempat_uji_kompetensi in Request Body")

		id_tempat_uji_kompetensi = data["id_tempat_uji_kompetensi"]

		# Cek apakah data skema sertifikasi ada
		query_temp = " SELECT id_tempat_uji_kompetensi FROM tempat_uji_kompetensi WHERE is_delete!=1 AND id_tempat_uji_kompetensi = %s "
		values_temp = (id_tempat_uji_kompetensi, )
		data_temp = dt.get_data(query_temp, values_temp)
		if len(data_temp) == 0:
			return defined_error("Gagal, data tidak ditemukan")

		query = """ UPDATE tempat_uji_kompetensi SET id_tempat_uji_kompetensi=id_tempat_uji_kompetensi """
		values = ()
		
		if "id_kota" in data:
			id_kota = data["id_kota"]
			
			# cek apakah data kota ada
			query_temp = "SELECT id_kota FROM kota WHERE is_delete!=1 AND id_kota = %s"
			values_temp = (id_kota, )
			data_temp = dt.get_data(query_temp, values_temp)
			if len(data_temp) == 0:
				return defined_error("Gagal, Data Kota tidak ditemukan")
			
			query += """ ,id_kota = %s """
			values += (id_kota, )

		if "nama_tempat_uji_kompetensi" in data:
			nama_tempat_uji_kompetensi = data["nama_tempat_uji_kompetensi"]	
			query += """ ,nama_tempat_uji_kompetensi = %s """
			values += (nama_tempat_uji_kompetensi, )

		if "deskripsi_tempat_uji_kompetensi" in data:
			deskripsi_tempat_uji_kompetensi = data["deskripsi_tempat_uji_kompetensi"]	
			query += """ ,deskripsi_tempat_uji_kompetensi = %s """
			values += (deskripsi_tempat_uji_kompetensi, )

		if "alamat" in data:
			alamat = data["alamat"]	
			query += """ ,alamat = %s """
			values += (alamat, )

		if "nomor_telepon" in data:
			nomor_telepon = data["nomor_telepon"]	
			query += """ ,nomor_telepon = %s """
			values += (nomor_telepon, )

		if "email" in data:
			email = data["email"]	
			query += """ ,email = %s """
			values += (email, )

		if "longitude" in data:
			longitude = data["longitude"]	
			query += """ ,longitude = %s """
			values += (longitude, )

		if "latitude" in data:
			latitude = data["latitude"]	
			query += """ ,latitude = %s """
			values += (latitude, )

		if "foto_tempat_uji_kompetensi" in data:
			filename_photo = secure_filename(now.strftime("%Y-%m-%d %H:%M:%S")+"_"+str(random_string_number_only(5))+"_foto_tempat_uji_kompetensi.png")
			save(data["foto_tempat_uji_kompetensi"], os.path.join(app.config['UPLOAD_FOLDER_FOTO_TEMPAT_UJI_KOMPETENSI'], filename_photo))

			foto_tempat_uji_kompetensi = filename_photo

			query += """ ,foto_tempat_uji_kompetensi = %s """
			values += (foto_tempat_uji_kompetensi, )

		if "is_aktif" in data:
			is_aktif = data["is_aktif"]
			# validasi data is_aktif
			if str(is_aktif) not in ["0", "1"]:
				return parameter_error("Invalid is_aktif Parameter")
			query += """ ,is_aktif = %s """
			values += (is_aktif, )

		if "is_delete" in data:
			is_delete = data["is_delete"]
			# validasi data is_delete
			if str(is_delete) not in ["1"]:
				return parameter_error("Invalid is_delete Parameter")
			query += """ ,is_delete = %s """
			values += (is_delete, )
		
		query += """ WHERE id_tempat_uji_kompetensi = %s """
		values += (id_tempat_uji_kompetensi, )
		dt.insert_data(query, values)

		hasil = "Berhasil mengubah data tempat uji kompetensi"
		try:
			logs = secure_filename(strftime("%Y-%m-%d %H:%M:%S"))+" - "+ROUTE_NAME+" - id_user = "+str(id_user)+" - roles = "+str(role)+"\n"
		except Exception as e:
			logs = secure_filename(strftime("%Y-%m-%d %H:%M:%S"))+" - "+ROUTE_NAME+" - id_user = NULL - roles = NULL\n"
		tambahLogs(logs)
		return make_response(jsonify({'status_code':200, 'description': hasil} ), 200)
	except Exception as e:
		return bad_request(str(e))

#endregion ================================= TEMPAT UJI KOMPETENSI AREA ==========================================================================


#region ================================= DAERAH AREA ==========================================================================

@lokasi.route('/get_provinsi', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_provinsi():
	try:
		ROUTE_NAME = str(request.path)
		
		dt = Data()

		query = """ SELECT a.* FROM provinsi a WHERE a.is_delete !=1 """
		values = ()

		page = request.args.get("page")
		id_provinsi = request.args.get("id_provinsi")
		search = request.args.get("search")
		is_aktif = request.args.get("is_aktif")
		limit = request.args.get("limit")
		order_by = request.args.get("order_by")

		# Validasi parameter limit
		if (limit == None or limit == ""):
			limit = 10
		try:
			limit = int(limit)
		except Exception as e:
			return parameter_error ("Invalid limit Parameter")
		# Parameter limit tidak boleh lebih kecil dari 1, kecuali -1 itu unlimited
		if limit != -1 and limit < 1:
			return parameter_error ("Invalid limit Parameter")
		
		if (page == None):
			page = 1
		if id_provinsi:
			query += " AND a.id_provinsi = %s "
			values += (id_provinsi, )
		if search:
			query += """ AND CONCAT_WS("|", a.nama_provinsi) LIKE %s """
			values += ("%"+search+"%", )
		if is_aktif:
			query += " AND a.is_aktif = %s "
			values += (is_aktif, )

		if order_by:
			if order_by == "id_asc":
				query += " ORDER BY a.id_provinsi ASC "
			elif order_by == "id_desc":
				query += " ORDER BY a.id_provinsi DESC "
			elif order_by == "nama_asc":
				query += " ORDER BY a.nama_provinsi ASC "
			elif order_by == "nama_desc":
				query += " ORDER BY a.nama_provinsi DESC "
			else:
				query += " ORDER BY a.nama_provinsi ASC "
		else:
			query += " ORDER BY a.nama_provinsi ASC "

		# return make_response(str(limit), 200)
		rowCount = dt.row_count(query, values)
		if str(limit) != "-1":
			hasil = dt.get_data_lim_param(query, values, page, limit)
		else:
			hasil = dt.get_data(query, values)
		hasil = {'data': hasil , 'status_code': 200, 'page': page, 'offset': str(limit), 'row_count': rowCount}
		########## INSERT LOG ##############
		imd = ImmutableMultiDict(request.args)
		imd = imd.to_dict()
		param_logs = "[" + str(imd) + "]"
		try:
			logs = secure_filename(strftime("%Y-%m-%d %H:%M:%S"))+" - "+ROUTE_NAME+" - id_user = "+str(id_user)+" - roles = "+str(role)+" - param_logs = "+param_logs+"\n"
		except Exception as e:
			logs = secure_filename(strftime("%Y-%m-%d %H:%M:%S"))+" - "+ROUTE_NAME+" - id_user = NULL - roles = NULL - param_logs = "+param_logs+"\n"
		tambahLogs(logs)
		####################################
		return make_response(jsonify(hasil),200)
	except Exception as e:
		return bad_request(str(e))

@lokasi.route('/get_kota', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_kota():
	try:
		ROUTE_NAME = str(request.path)
		
		dt = Data()

		query = """ SELECT a.*, b.nama_provinsi 
					FROM kota a
					LEFT JOIN provinsi b ON a.id_provinsi=b.id_provinsi
					WHERE a.is_delete != 1 """
		values = ()

		page = request.args.get("page")
		id_kota = request.args.get("id_kota")
		id_provinsi = request.args.get("id_provinsi")
		search = request.args.get("search")
		is_aktif = request.args.get("is_aktif")
		limit = request.args.get("limit")
		order_by = request.args.get("order_by")

		# Validasi parameter limit
		if (limit == None or limit == ""):
			limit = 10
		try:
			limit = int(limit)
		except Exception as e:
			return parameter_error ("Invalid limit Parameter")
		# Parameter limit tidak boleh lebih kecil dari 1, kecuali -1 itu unlimited
		if limit != -1 and limit < 1:
			return parameter_error ("Invalid limit Parameter")
		
		if (page == None):
			page = 1
		if id_kota:
			query += " AND a.id_kota = %s "
			values += (id_kota, )
		if id_provinsi:
			query += " AND a.id_provinsi = %s "
			values += (id_provinsi, )
		if search:
			query += """ AND CONCAT_WS("|", a.nama_kota) LIKE %s """
			values += ("%"+search+"%", )
		if is_aktif:
			query += " AND a.is_aktif = %s "
			values += (is_aktif, )

		if order_by:
			if order_by == "id_asc":
				query += " ORDER BY a.id_kota ASC "
			elif order_by == "id_desc":
				query += " ORDER BY a.id_kota DESC "
			elif order_by == "nama_asc":
				query += " ORDER BY a.nama_kota ASC "
			elif order_by == "nama_desc":
				query += " ORDER BY a.nama_kota DESC "
			else:
				query += " ORDER BY a.nama_kota ASC "
		else:
			query += " ORDER BY a.nama_kota ASC "

		# return make_response(str(limit), 200)
		rowCount = dt.row_count(query, values)
		if str(limit) != "-1":
			hasil = dt.get_data_lim_param(query, values, page, limit)
		else:
			hasil = dt.get_data(query, values)
		hasil = {'data': hasil , 'status_code': 200, 'page': page, 'offset': str(limit), 'row_count': rowCount}
		########## INSERT LOG ##############
		imd = ImmutableMultiDict(request.args)
		imd = imd.to_dict()
		param_logs = "[" + str(imd) + "]"
		try:
			logs = secure_filename(strftime("%Y-%m-%d %H:%M:%S"))+" - "+ROUTE_NAME+" - id_user = "+str(id_user)+" - roles = "+str(role)+" - param_logs = "+param_logs+"\n"
		except Exception as e:
			logs = secure_filename(strftime("%Y-%m-%d %H:%M:%S"))+" - "+ROUTE_NAME+" - id_user = NULL - roles = NULL - param_logs = "+param_logs+"\n"
		tambahLogs(logs)
		####################################
		return make_response(jsonify(hasil),200)
	except Exception as e:
		return bad_request(str(e))

#endregion ================================= DAERAH AREA ==========================================================================