import datetime
import sqlite3


class sqlWork:
	def __init__(self):
		self.connection = sqlite3.connect("kategoricar.db")
        	self.cursor = self.connection.cursor()

	def __del__(self):
		self.connection.close()
#####################################################################################################

	def returnData(self, sql):
		self.cursor.execute(sql)
		return self.cursor.fetchall()
		

	def updateData(self, mbo=None, kategorija=None, areacode=None, osnova=None, counter=None):
		if (kategorija!=None):
			self.cursor.execute("update testTable set kategorija=:Kate, podrucni=:Pon, osnova=:Osn, zadnjiUpdate=:Up where mbo=:Mbo ",{"Mbo": mbo, "Kate": kategorija, "Pon": areacode, "Osn":osnova,"Up":datetime.datetime.now()})

		else:
			self.cursor.execute("update testTable set counter = :Counter where mbo= :Mbo ",{"Mbo": mbo, "Counter": counter + 1})
	def deleteData(self, mbo):
		self.cursor.execute("delete from testTable where mbo=%s" % mbo)

	def insertData(self, mbo=None, kategorija=None, vrijeme=None, osnova=None, areacode=None):
		self.cursor.execute("insert into testTable values(?,?,?,?,?,?)", (mbo, kategorija, vrijeme, 0, osnova, areacode))
	
	def commitData(self):
		self.connection.commit()


########################
###### TEST'S ##########
########################

#sqlWork(1).insertData(mbo="1112", kategorija="A", vrijeme=datetime.datetime.now(), osnova="00413", areacode="004")
#print sqlWork().returnResults("select * from testTable where mbo='1112'")
#sqlWork(1).updateData(mbo="1112", counter=2)
#print sqlWork().returnData("select * from testTable where mbo='143520838'")
#sqlWork(1).updateData(mbo="143520838", kategorija="B", areacode="114", osnova="00112")
#print sqlWork().returnData("select * from testTable where mbo='143520838'")
#sqlWork().deleteData("1112")
#print sqlWork().returnResults("select * from testTable where mbo='1112'")
#sqlWork(1).deleteData("1112")
#print sqlWork().returnResults("select * from testTable where mbo='1112'")

