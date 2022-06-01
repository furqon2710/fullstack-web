import json
import os
from . import config as CFG
import mysql.connector

#koneksi ke database
def conn(user=CFG.DB_USER, password=CFG.DB_PASSWORD, host=CFG.DB_HOST, database=CFG.DB_NAME):
	conn = mysql.connector.connect(
		host=host,
		user=user,
		passwd=password,
		database=database
	)
	return conn

#Perintah Query Select ke JSON
def select(query, values, conn):
	mycursor = conn.cursor()
	mycursor.execute(query, values)
	row_headers = [x[0] for x in mycursor.description]
	myresult = mycursor.fetchall()
	json_data = []
	for result in myresult:
		json_data.append(dict(zip(row_headers, result)))
	return json_data

#Get single row
def select_row(query, values, conn):
	mycursor = conn.cursor(buffered=True)
	mycursor.execute(query, values)
	row_headers = [x[0] for x in mycursor.description]
	myresult = mycursor.fetchmany(1)
	json_data = []
	for result in myresult:
		json_data.append(dict(zip(row_headers, result)))
	return json_data

#Perintah Query Select ke JSON
def select_limit(query, values, conn, page=1):
	mycursor = conn.cursor()
	page = int(page)
	lim = 0
	off = 10
	if page == 1:
		lim = 0
	else: 
		lim = (page-1) * 10
	# return query + " limit "+str(lim)+", "+str(off)
	mycursor.execute(query + " limit "+str(lim)+", "+str(off) , values)
	row_headers = [x[0] for x in mycursor.description]
	myresult = mycursor.fetchall()
	json_data = []
	for result in myresult:
		json_data.append(dict(zip(row_headers, result)))
	return json_data

def select_limit_param(query, values, conn, page=1, off=10):
	mycursor = conn.cursor()
	page = int(page)
	lim = 0
	off = int(off)
	if page == 1:
		lim = 0
	else: 
		lim = (page-1) * off
	# return query + " limit "+str(lim)+", "+str(off)		
	mycursor.execute(query + " limit "+str(lim)+", "+str(off) , values)
	row_headers = [x[0] for x in mycursor.description]
	myresult = mycursor.fetchall()
	json_data = []
	for result in myresult:
		json_data.append(dict(zip(row_headers, result)))
	return json_data

def select2(query, values, conn):
	mycursor = conn.cursor()
	mycursor.execute(query, values)
	myresult = mycursor.fetchall()
	return myresult

# def select2(query, values, conn):
# 	mycursor = conn.cursor()
# 	mycursor.execute(query, values)
# 	row_headers = [x[0] for x in mycursor.description]
# 	myresult = mycursor.fetchall()
# 	return myresult, row_headers	

#Perintah Query Insert
def insert(query, val, conn):
	mycursor = conn.cursor()
	mycursor.execute(query,val)
	conn.commit()
	# mycursor.close()
	# conn.close()

#Perintah Query Insert
def insert2(query, val, conn):
	mycursor = conn.cursor()
	mycursor.execute(query,val)
	conn.commit()
	# mycursor.close()
	# conn.close()
	return mycursor.lastrowid

#Perintah Count
def row_count(query, conn):
	mycursor = conn.cursor()
	mycursor.execute(query)
	mycursor.fetchall()
	rc = mycursor.rowcount
	return rc

#Perintah Count plus filter
def row_count2(query, val,  conn):
	mycursor = conn.cursor()
	mycursor.execute(query, val)
	mycursor.fetchall()
	rc = mycursor.rowcount
	return rc
