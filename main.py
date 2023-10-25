from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog, QTableWidgetItem
import mysql.connector
from mysql.connector import errorcode
import pickle
from PyQt5.uic import loadUi
import sys
import csv
import datetime

class Main(QDialog):

    def __init__(self):
        super(Main, self).__init__()
        loadUi(r"Main.ui",self)
        self.setWindowTitle("Inventory Manager")
        # self.setWindowIcon(QtGui.QIcon(r"assets/icons/.svg"))
        self.lineEdit_pw.setEchoMode(QtWidgets.QLineEdit.Password)
        self.tabWidget.setTabEnabled(1,False)
        self.tabWidget.setTabEnabled(2,False)
        self.tabWidget.setTabEnabled(3,False)
        self.button_login.clicked.connect(self.connectSQL)
        self.button_logout.clicked.connect(self.logout)
        self.button_logout.setDisabled(True)
        connection_status = False
        self.label_usrupd.setText('')
        self.label_usrupd.adjustSize()

        self.tabWidget.tabBarClicked.connect(self.refresh_comboBoxes)
        self.button_revoke.clicked.connect(self.revoke_perms)
        self.button_grant.clicked.connect(self.grant_perms)
        self.label_filesave.setText('')
        self.checkBox_access.stateChanged.connect(self.block_db)

        self.button_import.clicked.connect(self.Import_CSV)
        self.button_export.clicked.connect(self.Export_CSV)
        self.spinBox_notify.valueChanged.connect(self.min_count)
        self.label_update.setText("")
        self.checkBox_desc.setChecked(True)
        self.checkBox_part_no.setChecked(True)
        self.checkboxstatus()

        self.button_search.clicked.connect(self.search)
        self.button_update.clicked.connect(self.updateTable)

    def search(self):
        query = self.lineEdit_search.text()
        quer = str(query)
        # search_in = ()
        try:
            if (self.checkBox_desc.isChecked() == True) and (self.checkBox_part_no.isChecked() == True):
                stmt = "Select sl_no, part_no, mfg_p_no, part_desc, qty, location from storage where (part_desc like "+'"%'+query+'%") or (part_no like '+'"%'+query+'%")'
                # print(stmt)
            elif (self.checkBox_desc.isChecked() == True) and (self.checkBox_part_no.isChecked() == False):
                # search_in.append('part_desc')
                 stmt = "Select sl_no, part_no, mfg_p_no, part_desc, qty, location from storage where part_desc like "+'"%'+query+'%"'
                 # print(stmt)
            elif (self.checkBox_desc.isChecked() == False) and (self.checkBox_part_no.isChecked() == True):
                # search_in.append('part_no')
                stmt = "Select sl_no, part_no, mfg_p_no, part_desc, qty, location from storage where part_no like "+'"%'+query+'%"'
                # print(stmt)

            cursor = self.cnx.cursor()
            cursor.execute(stmt)
            results = cursor.fetchall()

            self.tableWidget.setRowCount(len(results))
            for row, item in enumerate(results):
                c0 = QTableWidgetItem(str(item[0]))
                c1 = QTableWidgetItem(str(item[1]))
                c2 = QTableWidgetItem(str(item[2]))
                c3 = QTableWidgetItem(str(item[3]))
                c4 = QTableWidgetItem(str(item[4]))
                c5 = QTableWidgetItem(str(item[5]))
                self.tableWidget.setItem(row, 0, c0)
                self.tableWidget.setItem(row, 1, c1)
                self.tableWidget.setItem(row, 2, c2)
                self.tableWidget.setItem(row, 5, c3)
                self.tableWidget.setItem(row, 4, c4)
                self.tableWidget.setItem(row, 3, c5)
        except Exception as e:
            print(e)

    def updateTable(self):
        newqty = self.spinBox.value()
        slno = self.lineEdit_part.text()
        cursor1 = self.cnx.cursor()
        cursor1.execute("select qty from storage where sl_no = "+slno)
        qtl = cursor1.fetchall()
        cursor1.close()
        # print(qtl)
        qtl = qtl[0][0]
        newqty = qtl - newqty
        newqtyint = newqty
        newqty = str(newqty)
        cursor = self.cnx.cursor()
        cursor.execute("update storage set qty = "+newqty+" where sl_no = "+slno)
        current_date_and_time = datetime.datetime.now()
        dts = current_date_and_time.strftime(r"%Y-%m-%d_%H-%M")
        dts = str(dts)
        cursor.execute("update storage set last_upd_date = '"+dts+"' where sl_no = "+slno)
        cursor.execute("update storage set last_upd_usr = '"+usr0+"' where sl_no = "+slno)
        self.label_update.setText("Updated quantity. Refresh table")
        self.cnx.commit()
        cursor.close()
        #log
        logname = dts+".log"
        cursor = self.cnx.cursor()
        cursor.execute("select * from storage where sl_no = "+slno)
        rows = cursor.fetchall()
        # print(rows)
        with open(logname,'w') as log:
            for row in rows:
                # print(row)
                rowstr = str(row)
                log.write(rowstr)
                try:
                    with open(".db_count.bin",'rb') as filehandle:
                        mincount = pickle.load(filehandle)
                        mincount = mincount[0]
                        # print(mincount)
                        if newqtyint <= mincount:
                            with open("Orderlist.csv",'a') as orderlist:
                                csv_writer = csv.writer(orderlist)
                                csv_writer.writerow(row)
                except FileNotFoundError:
                    print()
        # self.cnx.commit()
        cursor.close()
        #notify if less items

    #to check if db access is blocked
    def checkboxstatus(self):
            try:
                fileh = open(".db_state.bin",'rb')
                dbst = pickle.load(fileh)
                if dbst == "Disabled":
                    self.checkBox_access.setChecked(True)
                    fileh.close()
            except FileNotFoundError:
                fileh = open(".db_state.bin",'wb')
                pickle.dump("Enabled",fileh)
                fileh.flush()
                fileh.close()
            except EOFError:
                fileh = open(".db_state.bin",'wb')
                pickle.dump("Enabled",fileh)
                fileh.flush()
                fileh.close()

    #notify thing; this fn updates dotfile
    def min_count(self):
        mincount = self.spinBox_notify.value()
        list1 = []
        list1.append(mincount)
        with open(".db_count.bin",'wb') as filehandle:
                pickle.dump(list1, filehandle)

    #disable db access
    def block_db(self):
        if self.checkBox_access.isChecked() == True:
            with open(".db_state.bin",'wb') as filehandle:
                pickle.dump("Disabled", filehandle)
        else:
            with open(".db_state.bin",'wb') as filehandle:
                pickle.dump("Enabled", filehandle)

        #manage users tab

    def refresh_comboBoxes(self, useless_arg):
        # cur = cnx.cursor()
        # print(self.tabWidget.currentIndex(),self.connection_status)
        # if (self.tabWidget.currentIndex() == 3) and (self.connection_status == True):
        if self.connection_status == True:
            # cur1 = self.cnx.cursor()
            # cur1.close()
            cur1 = self.cnx.cursor()
            cur1.execute("select * from users")
            userlist1 = cur1.fetchall()
            # print(self.userlist)

            self.comboBox_rev.clear()
            for admin_usr in userlist1:
                # print(admin_usr[0])
                if admin_usr[1] == 1:
                    self.comboBox_rev.addItem(admin_usr[0])

            self.comboBox_grt.clear()
            for user_usr in userlist1:
                if user_usr[1] == 0:
                    self.comboBox_grt.addItem(user_usr[0])

    def revoke_perms(self):
        cur2 = self.cnx.cursor()
        selection = self.comboBox_rev.currentText()
        selection = selection.lower()
        cur2.execute("update users set admin=0 where users = '"+selection+"'")
        self.cnx.commit()
        self.refresh_comboBoxes("useless_arg")
        self.label_usrupd.setText('Revoked admin permissions from '+selection+' successfully.')

    def grant_perms(self):
        # cur3 = self.cnx.cursor()
        # new_admin = self.lineEdit.text()
        # new_admin = new_admin.lower()
        # try:
        #     cur3.execute("insert into users values ('"+new_admin+"')")
        #     self.cnx.commit()
        #     self.refresh_comboBox_rev("useless_arg")
        #     self.label_usrupd.setText("Granted admin permissions to "+new_admin+"successfully.")
        # except mysql.connector.errors.IntegrityError:
        #     self.label_usrupd.setText("Error: User already exists")
        cur3 = self.cnx.cursor()
        selection0 = self.comboBox_grt.currentText()
        selection0 = selection0.lower()
        cur3.execute("update users set admin=1 where users = '"+selection0+"'")
        self.cnx.commit()
        self.refresh_comboBoxes("useless_arg")
        self.label_usrupd.setText('Granted admin permissions to '+selection0+' successfully.')

    #login part
    def connectSQL(self):
        global usr0
        usr0 = self.lineEdit_usr.text()
        pw = self.lineEdit_pw.text()
        hostname = self.lineEdit_host.text()
        global db
        db = self.lineEdit_db.text()

        try:
            global cnx
            self.cnx = mysql.connector.connect(host = hostname, user = usr0, password = pw, database = db)
            if ((self.cnx.is_connected) and (db.strip() != '')) :
                self.label_current_usr.setText("Logged in as: "+usr0+" | Connected to database: "+db)
                self.label_current_usr.adjustSize()
                self.button_logout.setDisabled(False)
                # self.tabWidget.setTabEnabled(1,True)
                self.connection_status = True

                try:
                    with open(".db_count.bin",'rb') as filehandle:
                        mincount = pickle.load(filehandle)
                        mincount = mincount[0]
                        self.spinBox_notify.setValue(mincount)
                except FileNotFoundError:
                    print()

                try:
                    fileh = open(".db_state.bin",'rb')
                    dbst = pickle.load(fileh)
                    # print(dbst)
                    if dbst == "Enabled":
                        self.tabWidget.setTabEnabled(1,True)
                        fileh.close()
                except FileNotFoundError:
                    fileh = open(".db_state.bin",'wb')
                    pickle.dump("Enabled",fileh)
                    fileh.flush()
                    fileh.close()
                except EOFError:
                    fileh = open(".db_state.bin",'wb')
                    pickle.dump("Enabled",fileh)
                    fileh.flush()
                    fileh.close()

                cur = self.cnx.cursor()
                cur.execute("create table IF NOT EXISTS users(users varchar(50) PRIMARY KEY, admin int)")
                cur.execute("select * from users")
                userlist = cur.fetchall()
                existinguser = False

                try:
                    for row in userlist:
                        if ((row[0] == usr0) and (row[1] == 1)) or (usr0 == 'root'):
                            self.tabWidget.setTabEnabled(2,True)
                            self.tabWidget.setTabEnabled(3,True)
                            existinguser = True
                            break
                        if (row[0] == usr0):
                            existinguser = True
                            break

                    if existinguser == False:
                        if usr0 == 'root':
                            cur.execute("insert into users values ('"+usr0+"',1 )")
                        else:
                            cur.execute("insert into users values ('"+usr0+"',0 )")
                        self.cnx.commit()
                        for row in userlist:
                            if ((row[0] == usr0) and (row[1] == 1)) or (usr0 == 'root'):
                                self.tabWidget.setTabEnabled(2,True)
                                self.tabWidget.setTabEnabled(3,True)
                                existinguser = True
                                break
                            if (row[0] == usr0):
                                existinguser = True
                                break
                        self.refresh_comboBoxes("useless_arg")
                        self.label_current_usr.setText("Logged in as: "+usr0+" | Connected to database: "+db+" | Added "+usr0+"to users list. Log in again")
                except:
                    print()


        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                self.label_current_usr.setText("username/password error")
                self.label_current_usr.adjustSize()
                self.button_logout.setDisabled(True)
                self.tabWidget.setTabEnabled(1,False)
                self.tabWidget.setTabEnabled(2,False)
                self.tabWidget.setTabEnabled(3,False)
                self.connection_status = False
            elif (err.errno == errorcode.ER_BAD_DB_ERROR):
                self.label_current_usr.setText("Database does not exist")
                self.label_current_usr.adjustSize()
                self.button_logout.setDisabled(True)
                self.tabWidget.setTabEnabled(1,False)
                self.tabWidget.setTabEnabled(2,False)
                self.tabWidget.setTabEnabled(3,False)
                self.connection_status = False
            else:
                self.label_current_usr.setText("Status: Unknown Error")
                self.label_current_usr.adjustSize()
                self.button_logout.setDisabled(True)
                self.tabWidget.setTabEnabled(1,False)
                self.tabWidget.setTabEnabled(2,False)
                self.tabWidget.setTabEnabled(3,False)
                self.connection_status = False

    def logout(self):
        self.cnx.close()
        self.button_logout.setDisabled(True)
        self.tabWidget.setTabEnabled(1,False)
        self.tabWidget.setTabEnabled(2,False)
        self.tabWidget.setTabEnabled(3,False)
        self.label_current_usr.setText("Logged in as:")
        connection_status = False

    def Import_CSV(self):
        try:
            # syntax: (self, window_title, default_directory ('' is current directory), file type (patterns))
            filename = QFileDialog.getOpenFileName(self, "Open File", '', "CSV Files (*.csv)")
            filename = filename[0]
            cursor = self.cnx.cursor()
            with open(filename, 'r') as csv_file:
                csv_reader = csv.reader(csv_file)
                header = next(csv_reader)
#                cursor.execute("create table  IF NOT EXISTS storage (sl_no int PRIMARY KEY, part_no int, mfg_p_no varchar(255), part_desc varchar(255), qty int, uom varchar(255), location varchar(255), last_upd_usr varchar(255), last_upd_date varchar(255))")
                cursor.execute("truncate storage")
                cursor.execute("create table  IF NOT EXISTS storage (sl_no int PRIMARY KEY, part_no varchar(255), mfg_p_no varchar(255), part_desc varchar(255), qty int, uom varchar(255), location varchar(255), last_upd_usr varchar(255), last_upd_date varchar(255))")
                for row in csv_reader:

                    # if len(row[3])>255:
                    #     descr = row[3]
                    #     descr = descr[:90]
                    #     row[3] = descr
                    for element_index in range(0,len(row)):
                        if row[element_index]=='':
                            row[element_index]=None
                    print(row)
                    # cursor.execute("insert into storage values "+str(tuple(row)))
                    query = 'insert into storage values (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
                    cursor.execute(query,tuple(row))
                    self.cnx.commit()
                self.label_filesave.setText('Imported CSV successfully')
        except FileNotFoundError:
            self.label_filesave.setText('File not found')

    def Export_CSV(self):
        filename = QFileDialog.getSaveFileName(self, "Save File", '', "CSV Files (*.csv)")
        filename = filename[0]
        cursor = self.cnx.cursor()
        cursor.execute('Select * from storage')
        query = cursor.fetchall()

        with open(filename, 'w') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Sl No', 'Part Number', 'MFG P/N', 'Description', 'Qty', 'UOM', 'Location', 'Last Updated By', 'Date'])
            csv_writer.writerows(query)
        self.label_filesave.setText('Exported to CSV successfully')


app = QApplication(sys.argv)
mainwindow = Main()
mainwindow.show()
app.exec_()
