from crypt import methods
from sys import argv
from flask import Blueprint,render_template,request,redirect,jsonify,Response
from os import makedirs
import pymongo
from flask.helpers import flash, send_file, url_for
from werkzeug.utils import secure_filename
import csv
from datetime import datetime
from shutil import make_archive,rmtree
from random import randint
from user.user import setAuthCode,setAdminInfo
admin=Blueprint('admin',__name__)
adminMsg={}
adminID=''
myClient = pymongo.MongoClient(r"") # Enter mongodb cloud database link here
adminDB=None
flag=-1
@admin.route("/authCode") 
def getAuthCode():
    authCode=str(randint(10,99))
    setAuthCode(authCode)
    vals={'code':authCode}
    return (vals)
def setInfo(info,msg):
    global adminID,adminDB,adminMsg
    adminID=info['ID']
    adminDB=myClient[adminID]
    adminMsg=msg
@admin.route('/atdClass')
def setUserInfo():
    colName='ss' 
    i =1
    try:
        dateToday=datetime.today().strftime("%d%m%Y")
        while dateToday+colName+str(i) in adminDB.list_collection_names():
            i=i+1
        colName='ss'
        colName+=str(i)
    except TypeError:
       return redirect(url_for('getAdminData'))
    setAdminInfo(adminID,dateToday+colName.replace('ss','class'),dateToday+colName)
    return '200'
@admin.route("/admin",methods=["GET","POST"])
def loadAdminPage():
    if request.method == 'GET':
        try:
            if adminMsg['1'] != "Login Successfull!":
                return redirect(url_for('getAdminData'))
        except KeyError:
            return redirect(url_for('getAdminData'))
    else: 
        saveUserPhoto(request)
    usrData=readUserData()
    return render_template("admin.html",usrData=usrData)
def readUserData():
    data={}
    colName='class'
    i =1
    dateToday=datetime.today().strftime("%d%m%Y")
    while dateToday+colName+str(i) in adminDB.list_collection_names():
        i=i+1
    colName+=str(i) if(i-1==0) else str(i-1)
    userCol = adminDB[dateToday+colName]
    for x in userCol.find():
        del x['_id']
        data.update(x)
    return data
def saveUserPhoto(request):
    userCol = adminDB["usersPhoto"]
    allowedExt=['jpg']
    try:
        request.files['file'] 
        fileName=request.files['file'].filename.rsplit('/')[-1]
        if fileName.rsplit('.')[1] in allowedExt:
            secureFileName=secure_filename(request.files['file'].filename)
            fileData=request.files['file']
            imgData=fileData.read()
            updateUserdata={'enrollNo':secureFileName.rsplit('.')[0]}
            vals = { "$set": { 'file':imgData } }
            userCol.update_one(updateUserdata,vals,upsert=True)
    except KeyError:
        pass
@admin.route('/refreshTable',methods=['GET','POST'])
def refreshTableData():
    global flag
    url = url_for('admin.loadAdminPage').replace('/admin','/refreshTable')
    if '/'+request.url.split('/',3)[-1] == url and request.method == "POST":
        flag=1
        return 'Success!'
    elif '/'+request.url.split('/',3)[-1] == url and flag == 1 and request.method == "GET":
        flag=0
        usrData=readUserData()
        return {"res":"true","userData":usrData}
    return {"res":"false"}     

@admin.route('/csv',methods=['GET'])
def downloadCSVFile():
    colName='class'
    i =1
    dateToday=datetime.today().strftime("%d%m%Y")
    while dateToday+colName+str(i) in adminDB.list_collection_names():
        i=i+1
    colName+=str(i) if(i-1==0) else str(i-1)
    try:
        atdCol=adminDB[dateToday+colName] 
        colName=['Enrollment ID','Attendance']
        atd=[]
        for x in atdCol.find():
            ids=list(x.keys())     
            ids.remove('_id')
            for id in ids:
                atd.append({'Enrollment ID':id,'Attendance':x[id]})
        with open(f'Attendance Record ID-{adminID}.csv', 'w') as csvfile:  
            writer = csv.DictWriter(csvfile, fieldnames = colName)     
            writer.writeheader() 
            writer.writerows(atd) 
        return send_file(f'Attendance Record ID-{adminID}.csv',mimetype='text/csv',as_attachment=True)
    except TypeError:
        return redirect(url_for('getAdminData'))
@admin.route('/uploadedUsrImg',methods=['GET'])
def downloadUploadedUserPhotos():
    colName='ss' 
    i =1
    try:
        dateToday=datetime.today().strftime("%d%m%Y")
        userCol=adminDB['usersPhoto'] 
        for x in userCol.find():
            imgData=x["file"]
            try:
                makedirs(f'uploaded-user-images ID-{adminID}')
            except FileExistsError:
                pass
            imgFilePath=f'./uploaded-user-images ID-{adminID}/'+x['enrollNo']+'.jpg'
            with open(imgFilePath,'wb') as imgFile:
                imgFile.write(imgData)
        try:
                make_archive(f'uploaded-user-image ID-{adminID}', 'zip',f'./uploaded-user-images ID-{adminID}')
        except FileNotFoundError:
            return('No Attendance was taken by Staff')
        rmtree(f'./uploaded-user-images ID-{adminID}')
        return send_file(f'./uploaded-user-image ID-{adminID}.zip',mimetype='application/zip',as_attachment=True)
    except (TypeError,AttributeError):
            return redirect(url_for('getAdminData'))
@admin.route('/usrImg',methods=['GET'])
def downloadUserPhotos():
    colName='ss'
    i =1
    try:
        dateToday=datetime.today().strftime("%d%m%Y")
        while dateToday+colName+str(i) in adminDB.list_collection_names():
            i=i+1
        colName='ss' 
        colName+=str(i) if(i-1==0) else str(i-1)
        userCol=adminDB[dateToday+colName] 
        for x in userCol.find():
            imgData=x["file"]
            try:
                makedirs(f'user-images ID-{adminID}')
            except FileExistsError:
                pass
            imgFilePath=f'./user-images ID-{adminID}/'+x['enrollNo']+'.jpg'
            with open(imgFilePath,'wb') as imgFile:
                imgFile.write(imgData)
        try:
            make_archive(f'user-image ID-{adminID}', 'zip',f'./user-images ID-{adminID}')
        except FileNotFoundError:
            return('No Attendance was taken by Staff')
        rmtree(f'./user-images ID-{adminID}')
        return send_file(f'user-image ID-{adminID}.zip',mimetype='application/zip',as_attachment=True)
    except (TypeError,AttributeError):
        return redirect(url_for('getAdminData'))
@admin.route('/acc',methods=['GET','POST'])
def createAcc():
    global adminDB
    credentials=request.form.to_dict()
    msg={}
    ID=credentials['ID']
    password=credentials['password']
    accType=credentials['accType']
    accCol=adminDB[accType]
    accExists=credentials['accExists'] 
    if(accType=="user" and len(ID) == 10 and len(password) == 4) or(accType=='adminUsers' and len(ID) == 4 and len(password) == 4):
        if accType =='adminUsers':
            adminDB=myClient[accType]
            accType='info'
            accCol=adminDB[accType]
        if accType in adminDB.list_collection_names():
            for x in accCol.find():
                try:
                    val=x[str(ID)]
                    userDetails={ "$set": {str(ID):str(password)} }
                    if accExists == "delete":                                      
                        accCol.delete_one({str(ID) : val})
                        msg="Account deleted successfully"
                        break
                    elif accExists == "update":
                        accCol.update_one({str(ID) : val},userDetails)
                        msg="Account details updated successfully"
                        break
                except KeyError:
                    accCol.insert_one({str(ID) :str(password)})
                    msg="Account created successfully"
                    break
        else:
            accCol.insert_one({str(ID) :str(password)})
            msg="Account created successfully"
    else:
        msg="Please fill account details properly"
    return {'1':msg}
def createDirs(col,adminID):
    try:
        dirPath=''
        if 'class' in col:
            index=col.index('class')
            dirPath=f'./Attendance - {adminID}/{col[0:8]}/'+' Class '+col[index+5:]
        else:
            index=col.index('ss')
            dirPath=f'./Attendance - {adminID}/{col[0:8]}/'+' Class '+col[index+2:]+'/ Attendance photos '
        makedirs(dirPath)
    except FileExistsError:
        pass
    return dirPath
@admin.route('/getAtdRecords')
def getAtdRecords():
    myclient = pymongo.MongoClient(r"") # Enter mongodb cloud database link here
    if adminID == None:
        return redirect(url_for('getAdminData'))
    adminDB = myclient[adminID]
    colList=adminDB.list_collection_names()
    sortedColList=[]
    try:
        colList.remove('usersPhoto')
    except ValueError:
        pass

    if(len(colList)>0):
        for col in colList: 
            if col[0:8] not in sortedColList and col[0:8].isnumeric():
                sortedColList.append(col[0:8])
        sortedColList.sort(key = lambda date: datetime.strptime(date,"%d%m%Y"),reverse=True)
        colLi=[]
        atdData=[]
        for col1 in sortedColList:
            for col2 in colList:
                if col1 in col2:
                    colLi.append(col2)
        try:
                makedirs(f'./Attendance - {adminID}')
        except FileExistsError:
                pass
        csvColNames=['Enrollment ID','Attendance']
        for col in colLi:
            userCol=adminDB[col]
            if 'class' in col:
                for x in userCol.find():
                    enrollNos=list(x.keys())
                    enrollNos.remove('_id')
                    for enrollNo in enrollNos:
                        atdData.append({'Enrollment ID':enrollNo,'Attendance':x[enrollNo]})
                path=createDirs(col,adminID)
                with open(path+'/Attendance.csv', 'w') as csvfile:  
                        writer = csv.DictWriter(csvfile,fieldnames=csvColNames)     
                        writer.writeheader() 
                        writer.writerows(atdData) 
                atdData=[]
            else:
                path=createDirs(col,adminID)
                for x in userCol.find():
                        imgFilePath=path+'/'+x['enrollNo']+'.jpg'
                        imgData=x["file"]
                        with open(imgFilePath,'wb') as imgFile:
                            imgFile.write(imgData)
        myclient.close()
        try:
            make_archive(f'Attendance - {adminID}', 'zip',f'./Attendance - {adminID}')
        except FileNotFoundError:
            return('No Attendance was taken by Staff')
        rmtree(f'./Attendance - {adminID}')
        return send_file(f'Attendance - {adminID}.zip',mimetype='application/zip',as_attachment=True)   
    else:
        return('No attendance has been taken yet')
@admin.route('/adminLogout')
def adminLogout():
    global adminMsg
    adminMsg['1']=None
    return redirect(url_for('getAdminData',argv=request.url.rsplit('/')[-2]))