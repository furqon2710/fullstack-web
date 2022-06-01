import os
config_path = os.path.abspath(os.path.join(__file__,"../.."))

import sys
sys.path.append(config_path)

import config as CFG
import requests
import datetime
import mysql.connector
import json
from jinja2 import Template
import random
import json

mydb = mysql.connector.connect(
    host = CFG.DB_HOST,
    user = CFG.DB_USER,
    passwd = CFG.DB_PASSWORD,
    database = CFG.DB_NAME
)
cursor = mydb.cursor()

CRON_ERROR_LOG_FOLDER_PATH = CFG.CRON_ERROR_LOG_FOLDER_PATH

BISAAIPAYMENT_BASE_URL 	= CFG.BISAAIPAYMENT_BASE_URL
BISAAIPAYMENT_KEY 		= CFG.BISAAIPAYMENT_KEY

def tambahLogsErrorCrontab(logs):
	# Create directory if not exists
	if os.path.exists(CRON_ERROR_LOG_FOLDER_PATH) == False:
		os.makedirs(CRON_ERROR_LOG_FOLDER_PATH)

	# Write Logss
	f = open(CRON_ERROR_LOG_FOLDER_PATH + "ERROR_" + datetime.datetime.now().strftime("%Y-%m-%d")+ ".txt", "a")
	f.write(logs)
	f.close()

def cek_pembayaran_customer_sertifikasi():
	FUNCTION_NAME = "cek_pembayaran_customer_sertifikasi"
	try:
		query = """ SELECT a.id_transaction_customer_sertifkasi, a.id_customer_sertifikasi, a.nomor_invoice, a.total_transaksi, c.nama_skema_sertifikasi, e.email
					FROM transaction_customer_sertifkasi a 
					LEFT JOIN customer_sertifikasi b ON a.id_customer_sertifikasi=b.id_customer_sertifikasi
					LEFT JOIN skema_sertifikasi c ON b.id_skema_sertifikasi=c.id_skema_sertifikasi
					LEFT JOIN customer d ON b.id_customer=d.id_customer
					LEFT JOIN user e ON d.id_user=e.id_user
					WHERE a.is_delete!=1 AND a.status_transaksi=0 AND a.service_code IS NOT NULL """ 
		values = ()

		cursor.execute(query, values)
		result = cursor.fetchall()

		for x in result:
			now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
			
			id_transaksi				= x[0]
			id_customer_sertifikasi 	= x[1]
			nomor_invoice				= x[2]
			total_transaksi				= x[3]
			name_skema_sertifikasi		= x[4]
			email 						= x[5]
			
			
			print (FUNCTION_NAME, id_transaksi, nomor_invoice, total_transaksi)
			
			url = BISAAIPAYMENT_BASE_URL+"/transaksi/get_transaksi_status?transaction_no=%s&payment_status=00" % (nomor_invoice) 
			payload = {}
			headers = {
				'X-API-KEY': BISAAIPAYMENT_KEY
			}

			response = requests.request("GET", url, headers=headers, data = payload)
			status_code = response.status_code
					
			if str(status_code) == '200':
				qq 				= "UPDATE transaction_customer_sertifkasi a, customer_sertifikasi b SET a.status_transaksi=1, a.waktu_dibayar=%s, b.is_aktif=1 WHERE a.id_customer_sertifikasi=b.id_customer_sertifikasi AND a.id_transaction_customer_sertifkasi = %s AND a.nomor_invoice = %s"
				vv 				= (now, id_transaksi, nomor_invoice)
				cursor.execute(qq,vv)
				mydb.commit()
	except Exception as e:
		logs_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		logs = logs_timestamp + "-- "+FUNCTION_NAME+" -- Error : " + str(e)
		tambahLogsErrorCrontab(logs)


def cek_expired_customer_sertifikasi():
	FUNCTION_NAME = "cek_expired_customer_sertifikasi"
	# Untuk cek apakah transaksi sudah expired atau belum beradasarkan field waktu_akhir_bayar
	try:
		now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)

		query = "SELECT id_transaction_customer_sertifkasi FROM transaction_customer_sertifkasi WHERE %s > waktu_akhir_bayar AND status_transaksi = 0"
		values = (now, )

		cursor.execute(query,values)
		result = cursor.fetchall()

		for x in result:
			id_transaksi = x[0]
			print (FUNCTION_NAME, id_transaksi)

			qq = "UPDATE transaction_customer_sertifkasi a, customer_sertifikasi b SET a.status_transaksi=2, b.is_aktif=0, b.is_delete=1 WHERE a.id_customer_sertifikasi=b.id_customer_sertifikasi AND id_transaction_customer_sertifkasi = %s"
			vv = (id_transaksi, )
			cursor.execute(qq,vv)
			mydb.commit()
	except Exception as e:
		logs_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		logs = logs_timestamp + " -- "+FUNCTION_NAME+" -- Error : " + str(e)
		tambahLogsErrorCrontab(logs)


# >>>>>>>>>>>>>>>>> FUNCTION CALLER <<<<<<<<<<<<<<<<<<<<<
cek_pembayaran_customer_sertifikasi()
cek_expired_customer_sertifikasi()