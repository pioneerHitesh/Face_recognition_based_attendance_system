
from flask import Blueprint, render_template,request,redirect
from io import BytesIO
import face_recognition
from flask.helpers import url_for
import cv2
import pymongo
from multiprocessing import Process
from requests import post
user=Blueprint('user',__name__)
msg={}
ID=''
adminID=''
atdMsg=''
trueAuthCode=''
colName=''
ssColName=''
Userprocess={}
def setAuthCode(authCode):
    global trueAuthCode
    trueAuthCode=authCode
def setAdminInfo(ID,col1,col2):
    global adminID,colName,ssColName
    adminID=ID
    colName=col1
    ssColName=col2
    
def faceImage(url):
    cap=cv2.VideoCapture(url)
    if cap.isOpened():
        ret,frame =cap.read()
        cap.release()
        if ret and frame is not None:
            isSuccess, imBufArr = cv2.imencode(".jpg",frame)
            if isSuccess == True:
                byteImg = imBufArr.tobytes()
                return byteImg

    return None
def checkCredentials(credientials):
    global msg,ID
    data={}
    myClient = pymongo.MongoClient(r"") # Enter mongodb cloud database link here
    adminDB=myClient[adminID]
    userCol=adminDB['user']
    data={}
    for user in userCol.find():
        tempData=list(user.keys())
        tempData.remove('_id')
        for x in tempData:
            data[x]=user[x]
    try:
        password=data[credientials["ID"]]
        if credientials["password"] != password:
            msg['1']="Incorrect Password"
        else:
            ID =credientials["ID"]
            msg['1'] = "Login Successfull!" 
    except KeyError:
        msg['1']="Invalid user ID"
    myClient.close()  
@user.route("/login",methods = ['GET', 'POST'])
def getFormData():
    if request.method=="POST":
        credentials=request.form.to_dict()
        checkCredentials(credentials)
        if msg['1'] == "Login Successfull!":
            p=Process(target=loadUserPage)
            return redirect(url_for('user.loadUserPage'))
        else:
            return render_template("login.html",msg=msg)
    else:
        return render_template("login.html",msg={'1':None})
def checkAuthCode(authCode):
    if trueAuthCode !='':
        if authCode == trueAuthCode:
            return True
        else:
            return False
    else:
        pass
def checkAttendance(url):
    global atdMsg
    myclient = pymongo.MongoClient(r"") # Enter mongodb cloud database link here
    adminDB = myclient[adminID]
    photoCol=adminDB['usersPhoto']
    atdCol=adminDB[colName]
    usrFace=faceImage(url)
    result=[]
    for img in photoCol.find():
        if img['enrollNo'] == ID and type(usrFace) != None:
            imgFile = face_recognition.load_image_file(BytesIO(img['file']))
            imgFace=face_recognition.face_locations(imgFile)
            imgFaceEncoding=face_recognition.face_encodings(imgFile,imgFace)
            userFaceFile=face_recognition.load_image_file(BytesIO(usrFace))
            userFace=face_recognition.face_locations(userFaceFile)
            userFaceEncoding=face_recognition.face_encodings(userFaceFile,userFace)
            for faceEncoding in userFaceEncoding:
                result.append(face_recognition.compare_faces(imgFaceEncoding,faceEncoding))
            atdSSCol=adminDB[ssColName]
            if result != []:
                for res in result[0]:
                    if res ==True:
                        atdMsg='You have been marked present.'
                        
                        if colName in adminDB.list_collection_names():
                            for x in atdCol.find():
                                try:
                                    val=x[str(ID)]
                                    userAtd={ "$set": {str(ID):'Present' } }
                                    atdCol.update_one({str(ID) : val},userAtd)
                                except KeyError:
                                    atdCol.insert_one({str(ID) :'Present'})
                        else:
                            atdCol.insert_one({str(ID) :'Present'})
                    else:
                        atdMsg='You have been marked absent.'
                        if colName in adminDB.list_collection_names():
                            for x in atdCol.find():
                                try:
                                    val=x[str(ID)]
                                    userAtd={ "$set": {str(ID):'Absent' } }
                                    atdCol.update_one({str(ID) : val},userAtd)
                                except KeyError:
                                    atdCol.insert_one({str(ID) :'Absent'})
                        else:
                            atdCol.insert_one({str(ID) :'Absent'})
                    updateUserdata={'enrollNo':str(ID)}
                    vals = { "$set": { 'file':usrFace } }
                    atdSSCol.update_one(updateUserdata,vals,upsert=True)
            else:
                atdMsg='face recognition has failed.'
    myclient.close() 
@user.route("/user",methods=["GET","POST"])
def loadUserPage():
    if request.method == 'GET':
        try:
            if msg['1'] != "Login Successfull!":
                return redirect(url_for('user.getFormData'))
        except KeyError:
            return redirect(url_for('user.getFormData'))
    else:
        userData=request.form.to_dict()
        res=checkAuthCode(userData["authCo"])
        if res:
            checkAttendance(userData['userImg'])
            return redirect(url_for('user.loadAtdPage')) 
        else:
            return render_template("user.html",code={'1':"Invalid Code"})
    return render_template("user.html",code={'1':None})
@user.route("/usrAtd",methods=["GET"])
def loadAtdPage():
    if atdMsg == '':
        return redirect(url_for('user.loadUserPage'))
    else:
        if atdMsg != 'face recognition has failed.':
            url = request.url.replace('/usrAtd','/refreshTable')
            post(url)
        return render_template("userAtd.html",code={'1':atdMsg})
@user.route('/usrLogout')
def userLogout():
    global msg,atdMsg
    msg['1']=None
    atdMsg=''
    return redirect(url_for('user.getFormData'))


