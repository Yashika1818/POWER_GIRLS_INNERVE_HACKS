
from tkinter import Y
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from matplotlib.ft2font import BOLD 
from wtforms import StringField, PasswordField, BooleanField,SubmitField
from wtforms.validators import InputRequired, Email, Length,DataRequired
from flask_sqlalchemy  import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pdfkit
from werkzeug.utils import secure_filename
from flask import Response,make_response
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session ,url_for
from flask_session.__init__ import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from MyQR import myqr
import face_recognition                                                                                                                                                                                                     
from PIL import Image
import os
from base64 import b64decode
import re
import cv2
import pyzbar.pyzbar as pyzbar
from datetime import date, datetime

app = Flask(__name__)

app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydb.db'
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
db1 = SQLAlchemy(app)




class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])



faceDetect=cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))

        return '<h1>Invalid username or password</h1>'
   

    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect('/pdf_template')
     

    return render_template('signup.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    our_users = Usa.query.filter_by(name=current_user.username).first()
    # print(type(our_users.Roll_Number))
    return render_template('dashboard.html', name=current_user.username,our_users=our_users)

@app.route('/attendance')
def attendance():
    return render_template('attendance.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

class Usa(db1.Model):
    Roll_Number = db1.Column(db1.Integer,primary_key=True)
    name = db1.Column(db1.String(200),nullable=False)
    gender = db1.Column(db1.String(200),nullable=False)
   

class UserForm(FlaskForm):
    Roll_Number=StringField("RollNo : ",validators=[DataRequired()])
    name=StringField("Name ",validators=[DataRequired()])
    gender=StringField("Gender ",validators=[DataRequired()])
    submit=SubmitField("Submit")

@app.route('/pdf_template', methods=['GET', 'POST'])
def pdf_template():
    form=UserForm()
    if request.method == "POST":
        # user_rollno=request.form['Roll_No']
        user_name=request.form['name']
        user_gender=request.form['gender']


        output= request.form.to_dict()
        user_rollno= output["Roll_No"]
        with open('students.txt','a+') as f:
            f.write('\n')
            f.write(user_rollno)
            
            
        
        f = open('students.txt','r')
        lines = f.read().split("\n")
        print(lines)

        for _ in range (0,len(lines)):
            data = lines[_]
            version,level,qr = myqr.run(
                str(data),
                level='H',
                version=1,
                picture="Bg.png",
                colorized=True,
                contrast=1.0,
                brightness=1.0,
                save_name = str(lines[_]+'.png'),
                save_dir=os.getcwd()
                )

        new_user=Usa(Roll_Number=user_rollno,name=user_name,gender=user_gender)
        print("new user added")
        try: 
            db1.session.add(new_user)
            db1.session.commit()
            print("comitted")
            our_users = Usa.query.filter_by(Roll_Number=user_rollno).first()
            print(our_users.Roll_Number)
            rendered=render_template('id_card.html',our_users=our_users)
            pdf=pdfkit.from_string(rendered,False)
            response=make_response(pdf)
            response.headers['Content-Type']='application/pdf'
            response.headers['Content-Disposition']='inline; filename=output.pdf'
            return response
        except:
            return "there was an error adding"
    
    name=form.name.data
    form.name.data=''   
    our_users = Usa.query.filter_by(Roll_Number='168').first()
    return render_template('pdf_template.html',form=form,our_users=our_users)

@app.route("/facesetup", methods=["GET", "POST"])
def facesetup():
    if request.method == "POST":


        encoded_image = (request.form.get("pic"))
        username=current_user.username
        
        # compressed_data = zlib.compress(encoded_image, 9) 
        
        # uncompressed_data = zlib.decompress(compressed_data)
        # decoded_data = b64decode(uncompressed_data)
        decodedObjects = pyzbar.decode(encoded_image)
        for obj in decodedObjects:
            print(obj)
           
           
        new_image_handle = open('./static/face/unknown/'+str(username)+'.png', 'wb')
        
        # new_image_handle.write(decoded_data)
        new_image_handle.close()
       
        return redirect("/dashboard")

    else:
        return render_template("face.html")
names=[]
today=date.today()
d= today.strftime("%b-%d-%Y")


def checkData(data):
        # data=str(data)    
        if data in names:
            print('Already Present')
        else:
            print('\n'+str(len(names)+1)+'\n'+'present...')
            enterData(data)
def enterData(z):   
        if z in names:
            pass
        else:
            it=datetime.now()
            names.append(z)
            print("z is ")
            print(z)
            y=z
            z=''.join(str(z))
            intime = it.strftime("%H:%M:%S")
            print(intime)
            print(z)
            fob=open(d+'.xls','a+')
            fob.write(z+'\t'+intime+'\n')
            fob.close()
            #print(y+"is")
        return names 


class Video(object):
    
    
    def __init__(self):
        self.video=cv2.VideoCapture(0)
    def __del__(self):
        self.video.release()
    global count
    global BOL
    BOL=0
    count=0
    def get_frame(self):
        global count
        ret,frame=self.video.read()
        decodedObjects = pyzbar.decode(frame)
        for obj in decodedObjects:
            print(obj)
            checkData(obj.data)
         
            
        ret,jpg=cv2.imencode('.jpg',frame)
        return jpg.tobytes()





def gen(Video):
    global count
    print("genvideo ke andar")
    while True:
        
        frame=Video.get_frame()
        yield(b'--frame\r\n'
       b'Content-Type:  image/jpeg\r\n\r\n' + frame +
         b'\r\n\r\n')
    




@app.route('/video')

def video():
    fob=open(d+'.xls','a+')
    fob.write("Reg No."+'\t')
    fob.write("In Time"+'\n')
    # fob.write("Attendance")
    fob.close()
    global BOL
    print("video ke andar")
    return Response(gen(Video()),mimetype='multipart/x-mixed-replace; boundary=frame')

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("error.html",e = e)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == '__main__':
      app.run()



