from os import name
from random import randint
from flask import Flask,render_template,request,redirect
from flask.helpers import url_for
import pymongo
from admin.admin import admin, setInfo
from user.user import user
myClient = pymongo.MongoClient(r"") # Enter mongodb cloud link here
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
app.secret_key='221'
randomNums=[]
def checkCredentials(credientials):
    adminID=credientials['ID']
    adminMsg={}
    data={}
    adminUsers = myClient['adminUsers']
    info = adminUsers["info"]
    for x in info.find():
        del x['_id']
        data.update(x)
    try:
        password=data[credientials["ID"]]
        if credientials["password"] != password:
            adminMsg['1']="Incorrect Password"
        else:
            adminID =credientials["ID"]
            adminDB = myClient[adminID]  
            adminMsg['1'] = "Login Successfull!" 
    except KeyError:
        adminMsg['1']="Invalid user ID"
    return adminMsg
def registerBlueprint():
    global randomNums
    randomNum=''
    while(1):
        randomNum=str(randint(10,2000010))
        if randomNum not in randomNums:
            randomNums.append(randomNum)
            break
    app.register_blueprint(admin,url_prefix='/'+randomNum)
    app.register_blueprint(user,url_prefix='/'+randomNum)
@app.route("/",methods = ['GET', 'POST'])
def getAdminData():
    global randomNums
    if request.method=="POST":
        credentials=request.form.to_dict()
        adminMsg=checkCredentials(credentials)
        setInfo(credentials,adminMsg)
        if adminMsg['1'] == "Login Successfull!":
            return redirect(url_for('admin.loadAdminPage'))
        else:
            return render_template("admin-login.html",adminMsg=adminMsg)
    else:
        try:
            randomNums.remove(request.args['argv'])
        except (KeyError,ValueError):
            pass
        return render_template("admin-login.html",adminMsg={'1':None})
if __name__ == '__main__':
    registerBlueprint()
    app.run()