from . database import conn, select, select2, insert, insert2, row_count2, select_limit, select_limit_param, select_row

#Class 
class Data:
	def __init__(self):
		self.mydb = conn()

	# GET
	def get_data(self, query, values):
		return select(query, values, self.mydb)

	def get_data2(self, query, values):
		return select2(query, values, self.mydb)	

	def get_data_row(self, query, values):
		return select_row(query, values, self.mydb)	
	
	def get_data_lim(self, query, values, page):
		return select_limit(query, values, self.mydb, page)

	def get_data_lim_param(self, query, values, page, off):
		return select_limit_param(query, values, self.mydb, page, off)

	# INSERT / UPDATE
	def insert_data(self, query, val):
		return insert(query, val, self.mydb)

	def insert_data_last_row(self, query, val):
		return insert2(query, val, self.mydb)

	# ROW COUNT
	def row_count(self, query , val ):
		return row_count2(query , val, self.mydb)

	#Fungsi ambil data login
	def get_login(self, query, values):
		mycursor = self.mydb.cursor()
		mycursor.execute(query, values)
		row_headers = [x[0] for x in mycursor.description]
		myresult = mycursor.fetchall()
		return myresult

	def get_user(self, query, values):
		return select(query, values, self.mydb)