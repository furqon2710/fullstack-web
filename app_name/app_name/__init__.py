# -*- coding: utf-8 -*-
import sys
from flask import Flask, jsonify, request, make_response, render_template, redirect, session
from flask_session import Session
from flask_jwt_extended import create_access_token, get_jwt, jwt_required, JWTManager
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
from time import gmtime, strftime
import hashlib
from . matakuliah.controller import get_krs,get_mk
from . data import Data
from . import config as CFG


## IMPORT BLUEPRINT
# from .contoh_blueprint.controllers import contoh_blueprint
from .user.controllers import parameter_error, user
from .matakuliah.controller import matakuliah
from .absensi.controller import absensi
#region >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> CONFIGURATION <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
app = Flask(__name__, static_url_path=None) #panggil modul flask
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# #endregion >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> CONFIGURATION <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


# #region >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> FUNCTION AREA <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\
#endregion >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> FUNCTION AREA <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


#region >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> AUTH AREA (JWT) <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
@app.route("/")
@app.route("/index")
def index():
    if session['id_user'] !=None:
        print('berhasil login')
        if session['role'] == 1:
            user =  session
            matkul = get_mk(session['nip'])
            return render_template('dashboard_dosen.html',user=user,matkul = matkul)
        else:
            hasil  =  get_krs(session['id_user'])
            user =  session
            matkul = [
                {
                'judul' : 'Kalkulus 1',
                'deskripsi' : 'Senin 13.00 - 15.00'
                },
                {
                'judul' : 'Kalkulus 1',
                'deskripsi' : 'Senin 13.00 - 15.00'
                },
                {
                'judul' : 'Kalkulus 1',
                'deskripsi' : 'Senin 13.00 - 15.00'
                },
                {
                'judul' : 'Kalkulus 1',
                'deskripsi' : 'Senin 13.00 - 15.00'
                }
                ]
            return render_template('dashboard_mahasiswa.html',user=user,matkul=hasil)
    else:
        print('hit')
        return redirect('/login')
        
@app.route('/login')
def login():
    return render_template('login_template.html')
@app.route('/login_user',methods =['POST','GET'])
def login_user():
    print("hehe")
    email = request.args.get("email")
    password =  request.args.get('pass')
    dt = Data()
    password_enc = hashlib.md5(password.encode('utf-8')).hexdigest() # Convert password to md5
    query  = "SELECT * FROM user WHERE email=%s and password=%s"
    values =  (email,password_enc)
    hasil = dt.get_data(query,values)
    print('pass query1')
    if len(hasil) != 0:
        session['nama'] = hasil[0]['nama']
        session['role'] = hasil[0]['role']
        session['id_user'] = hasil[0]['id_user']
        print (session)
        if session['role'] == 2:
            query2 =  "SELECT * FROM mahasiswa WHERE id_user= %s "
            values2 = (hasil[0]['id_user'],)
            hasil2 = dt.get_data(query2,values2)
            print(hasil2)
            session['nim'] = hasil2[0]['nim']
        elif session['role'] == 1:
            query2 =  "SELECT * FROM dosen WHERE id_user= %s "
            values2 = (hasil[0]['id_user'],)
            hasil2 = dt.get_data(query2,values2)
            session['nip'] = hasil2[0]['nip']
        return redirect('/')
    else:
        return "Invalid email or password"
@app.route('/logout')
def logout():
    session['id_user'] = None
    session['nama'] = None
    session['role'] =  None
    session['nim'] =  None
    session['nip']  =None
    return redirect('/')
# #endregion >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> AUTH AREA (JWT) <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


# #region >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> INDEX ROUTE AREA <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<



# #endregion >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> INDEX ROUTE AREA <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


# #region >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ERROR HANDLER AREA <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# # fungsi error handle Halaman Tidak Ditemukan
# @app.errorhandler(404)
# @cross_origin()
# def not_found(error):
# 	return make_response(jsonify({'error': 'Tidak Ditemukan','status_code':404}), 404)

# #fungsi error handle Halaman internal server error
# @app.errorhandler(500)
# @cross_origin()
# def not_found(error):
# 	return make_response(jsonify({'error': 'Error Server','status_code':500}), 500)

#endregion >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ERROR HANDLER AREA <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


#--------------------- REGISTER BLUEPRINT ------------------------

app.register_blueprint(user, url_prefix='/user')
# app.register_blueprint(lokasi, url_prefix='/lokasi')
app.register_blueprint(matakuliah, url_prefix='/matakuliah')
app.register_blueprint(absensi, url_prefix='/absensi')

#--------------------- END REGISTER BLUEPRINT ------------------------
