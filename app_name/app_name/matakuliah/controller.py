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

matakuliah =  Blueprint('blueprint',__name__)



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


# region ============================================== MATA KULIAH AREA =============================
@matakuliah.route('/',methods=['GET'])
def nilai():
    return 'Blueprint Matakuliah'

@matakuliah.route('/insert_mk',methods = ['POST'])
def insert_mk():
    try :
        dt = Data()
        data = request.json
        if 'judul' not in data:
            return parameter_error('Missing judul in request body')
        if 'semester' not in data:
            return parameter_error('Missing semester in request body')
        if 'kelas' not in data:
            return parameter_error('Missing kelas in request body')
        if 'hari' not in data:
            return parameter_error("missing hari in request body")
        judul =  data['judul']
        semester =  data['semester']
        kelas =  data['kelas']
        hari =  data['hari']
        query =  "INSERT INTO `mata kuliah`(judul,semester, kelas, hari) VALUES(%s,%s,%s,%s)"
        values =  (judul,semester,kelas,hari,)
        dt.insert_data(query,values)
        return('MK berhasil dibuat')
    except Exception as e:
        return bad_request(str(e))

@matakuliah.route('/get_peserta_kelas',methods=['GET'])
def get_kelas():
	try:
		hasil = "Data Tidak ditemukan"
		data =  request.json
		kode_mk = data['kode mk']
		return(hasil)

	except Exception as e:
		return bad_request(str(e))
# endregion =========================================================== MATA KULIAH AREA =====================


# region ============================================================= KRS ===================================
@matakuliah.route('/create_krs',methods=['POST'])
def create_krs():
    try :
        dt = Data()
        data =  request.json
        if 'nim' not in data:
            return parameter_error('Missing nim in request body')
        if 'kode mk' not in data:
            return parameter_error('Missing kode mk in request body')
        if 'semester' not in data:
            return parameter_error('Missing semester in request body')
        nim  =  str(data['nim'])
        kode_mk =  data['kode mk']
        semester =  data['semester']
        print(nim)
        query  = "INSERT INTO krs(nim,`kode mk`,semester) VALUES(%s,%s,%s)"
        values = (nim,kode_mk,semester)
        print(query)
        print(values)
        dt.insert_data(query,values)
        return("KRS berhasil dibuat")
    except Exception as e:
        return bad_request(str(e))


# endregion ========================================================== KRS ==================================