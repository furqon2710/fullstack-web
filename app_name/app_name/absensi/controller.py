# from crypt import methods
# from crypt import methods
from cProfile import label
from flask import Blueprint, jsonify, request, make_response, render_template
from flask import current_app as app
from sklearn.svm import SVR
# from pytest import param
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
import matplotlib.pyplot as plt
import os
import numpy as np
import base64
import random
import json
import warnings
import string
import joblib
# import example.gps_solve
from .  example import gps_solve
from . models import Data

absensi =  Blueprint('absensi',__name__)
# import os
SVR_ant0 = joblib.load('SVR_ant0.sav')
SVR_ant1 =  joblib.load('SVR_ant1.sav')
SVR_ant2 =  joblib.load('SVR_ant2.sav')
SVR_ant3 =  joblib.load('SVR_ant3.sav')
SVR_ant = [SVR_ant0,SVR_ant1,SVR_ant2,SVR_ant3]
Scaler_ant0 =  joblib.load('Scaler_Ant0.sav')
Scaler_ant1 =  joblib.load('Scaler_Ant1.sav')
Scaler_ant2 =  joblib.load('Scaler_ant2.sav')
Scaler_ant3  =  joblib.load('Scaler_Ant3.sav')
Scaler =  [Scaler_ant0,Scaler_ant1,Scaler_ant2,Scaler_ant3]
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

def rssi_to_range(rssi,svr_model):
    jarak =  svr_model.predict(rssi)
    return jarak
def predict_coordinate(jarak):
    antena0 = [43,45]
    antena1 = [44,-47]
    antena2 = [-46,-48]
    antena3 = [-39,40]
    antena_coordinaate = [antena0,antena1,antena2,antena3]
    coordinate = []
    new_jarak = []
    for i in range(len(jarak)):
        if jarak[i] == 0:
            continue
        else:
            new_jarak.append(jarak[i])
            coordinate.append(antena_coordinaate[i])
    hasil  = gps_solve(new_jarak,coordinate)
    x  = hasil[0]
    y  =  hasil[1]
    return x,y
#endregion ================================= FUNGSI-FUNGSI AREA =============================================================
# region =============================  ABSENSI ===============================================
@absensi.route('/',methods= ['GET'])
def homepage():
    return'Blueprint Absensi'

@absensi.route('/create_absensi',methods = ['GET'])
def create_absensi():
    dt =  Data()
    data =  request.json
    if 'kode mk' not in data:
        return parameter_error('Missing kode mk in request body')
    if 'pertemuan ke' not in data:
        return parameter_error('Missing `pertemuan ke` in request body')
    kode_mk =  data['kode mk']
    pertemuan = data['pertemuan ke']
    query  =  "SELECT * FROM krs WHERE `kode mk` =  %s "
    values =  (kode_mk,)
    hasil = dt.get_data(query,values)
    for mahasiswa in hasil:
        nim =  mahasiswa['nim']
        query =  "SELECT * FROM absensi WHERE `kode mk`=%s AND nim=%s "
        values =  (kode_mk,nim,)
        row = dt.row_count(query,values)
        if row!=0:
            continue
        query = "INSERT INTO absensi(`kode mk`,nim,`pertemuan ke`,status) VALUES(%s,%s,%s,%s)"
        values =  (kode_mk,nim,pertemuan,0)
        dt.insert_data(query,values)
    return("Absensi Pertemuan ke "+pertemuan+" Berhasil dibuat")
@absensi.route('/edit_absensi', methods=['POST'])
def edit_absensi():
    dt =  Data()
    data =  request.json
    if 'status' not in data:
        return parameter_error('Missing status in request body')
    if 'nim' not in data:
        return parameter_error("Missing nim in Request body")
    if 'kode mk' not in data:
        return parameter_error("Missing kode mk in request body")
    if 'pertemuan' not in data:
        return parameter_error("Missing pertemuan in Request Body")
    status =  data['status']
    kode_mk =  data['kode mk']
    nim =  data['nim']
    pertemuan =  data['pertemuan']
    query = "UPDATE absensi SET status=%s WHERE `kode mk`=%s AND nim=%s AND `pertemuan ke`=%s "
    values =  (status, kode_mk,nim,pertemuan,)
    dt.insert_data(query,values)
    return("Edit Data Berhasil!")

@absensi.route('/get_absensi_dosen')
def get_absensi_dosen():
    hasil =  'data tidak ditemukan'
    dt = Data()
    data =  request.json
    if 'kode mk' not in data:
        return parameter_error("Missing kode mk in request body")
    if 'pertemuan ke' not in data:
        return parameter_error("Missing pertemuan ke in request body")
    kode_mk =  data['kode mk']
    pertemuan =  data['pertemuan']
    query =  "SELECT * FROM absensi WHERE `kode mk` =%s AND `pertemuan ke`=%s"
    values =  (kode_mk,pertemuan)
    dt.get_data(query,values)
    return(jsonify(hasil))



# endregion ========================== ABSENSI ================================================

# region ============================= SCAN ROOM ================================================
@absensi.route('/scan_room',methods=['GET','POST'])
def scan_room():
    dt = Data()
    data =  request.json
    if 'kode mk' not in data:
        return parameter_error("Missing kode mk in request body")
    kode_mk =  data['kode mk']
    scan_attempt = data['scan_attempt']
    # return jsonify(kode_mk)
    query =  "SELECT * FROM `rfid scan` WHERE `scan_attempt`=%s"
    values =  (scan_attempt,)
    hasil = dt.get_data(query,values)
    # return jsonify(hasil)
    x1 = []
    y1 = []
    namanama = []
    for data in hasil:
        rssi = []
        print(data)
        id_tag =  data['id_tag']
        rssi.append(data['ant0'])
        rssi.append(data['ant1'])
        rssi.append(data['ant2'])
        rssi.append(data['ant3'])
        jarak = []
        for i in range(len(rssi)):
            if rssi[i] == 0 :
                jarak.append(0)
            else:
                x =  rssi[i]
                x =  np.asarray(x).reshape(-1,1)
                scaler =  Scaler[i]
                sc_x  =  scaler.transform(x)
                jarak.append(rssi_to_range(sc_x,SVR_ant[i]))
        hasil_x,hasil_y= predict_coordinate(jarak)
        query =  "UPDATE `rfid scan` SET x=%s,y=%s WHERE id_tag=%s AND scan_attempt=%s"
        # print(hasil_x,hasil_y)
        hasil_x = int(hasil_x)
        hasil_y =  int(hasil_y)
        values =  (hasil_x,hasil_y,id_tag,scan_attempt)
        x1.append(hasil_x)
        y1.append(hasil_y)
        dt.insert_data(query,values)
        query = "SELECT nama FROM `rfid scan` LEFT JOIN `mahasiswa` ON `rfid scan`.`id_tag` = `mahasiswa`.`id_tag` LEFT JOIN `user` ON `mahasiswa`.`id_user` = `user`.`id_user` WHERE `rfid scan`.`id_tag` = %s"
        values = (id_tag,)
        nama =  dt.get_data(query,values)
        nama = nama[0]['nama']
        namanama.append(nama)
    filename ="scan_"+scan_attempt+".jpg"
    for i in range(len(x1)):
        plt.scatter(x1[i],y1[i])
    plt.legend(namanama)
    plt.yticks(np.arange(-80,90,20))
    plt.xticks(np.arange(-80,90,20))
    plt.savefig(filename)
    return("Scan Room Berhasil")
# endregion ========================== SCAN ROOM ================================================
