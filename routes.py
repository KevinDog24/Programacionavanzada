from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask import current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db
from .models import User, Question, Answer
from itsdangerous import URLSafeTimedSerializer
from email.mime.text import MIMEText
import smtplib
import re

bp = Blueprint('routes', __name__)

def validate_password(password):
   if len(password) < 8:
       return False
   if not re.search("[a-z]", password):
       return False
   if not re.search("[A-Z]", password):
       return False
   if not re.search("[0-9]", password):
       return False
   return True

@bp.route('/')
def index():
   questions = Question.query.order_by(Question.date_posted.desc()).all()
   return render_template('home.html', questions=questions)

@bp.route('/register', methods=['GET', 'POST'])
def signup():
   if request.method == 'POST':
       username = request.form['username']
       email = request.form['email']
       password = request.form['password']
       
       if not validate_password(password):
           flash('La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número')
           return redirect(url_for('routes.signup'))
           
       if User.query.filter_by(username=username).first():
           flash('Usuario ya existe')
           return redirect(url_for('routes.signup'))
           
       if User.query.filter_by(email=email).first():
           flash('Email ya registrado')
           return redirect(url_for('routes.signup'))
           
       user = User(username=username, email=email, password_hash=generate_password_hash(password))
       db.session.add(user)
       db.session.commit()
       flash('Registro exitoso')
       return redirect(url_for('routes.signin'))
   return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def signin():
   if request.method == 'POST':
       user = User.query.filter_by(username=request.form['username']).first()
       if user and check_password_hash(user.password_hash, request.form['password']):
           login_user(user)
           return redirect(url_for('routes.index'))
       flash('Usuario o contraseña incorrectos')
   return render_template('login.html')

@bp.route('/forgot', methods=['GET', 'POST'])
def forgot():
   if request.method == 'POST':
       email = request.form['email']
       user = User.query.filter_by(email=email).first()
       if user:
           s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
           token = s.dumps(email, salt='recover-key')
           send_reset_email(email, token)
           flash('Se envió un email con instrucciones')
       return redirect(url_for('routes.signin'))
   return render_template('forgot.html')

def send_reset_email(email, token):
   msg = MIMEText(f'Tu link de recuperación: http://localhost:5000/reset/{token}')
   msg['Subject'] = 'Recuperar Contraseña'
   msg['From'] = 'tu_email@gmail.com'
   msg['To'] = email
   
   s = smtplib.SMTP('smtp.gmail.com', 587)
   s.starttls()
   s.login('tu_email@gmail.com', 'tu_contraseña')
   s.send_message(msg)
   s.quit()

@bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset(token):
   try:
       s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
       email = s.loads(token, salt='recover-key', max_age=3600)
   except:
       flash('Link inválido o expirado')
       return redirect(url_for('routes.signin'))
       
   if request.method == 'POST':
       user = User.query.filter_by(email=email).first()
       password = request.form['password']
       if validate_password(password):
           user.password_hash = generate_password_hash(password)
           db.session.commit()
           flash('Contraseña actualizada')
           return redirect(url_for('routes.signin'))
       flash('La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número')
   return render_template('reset.html')

@bp.route('/question/<int:id>', methods=['GET', 'POST'])
def view_question(id):
   question = Question.query.get_or_404(id)
   if request.method == 'POST' and current_user.is_authenticated:
       answer = Answer(content=request.form['content'],
                      author=current_user,
                      question=question)
       db.session.add(answer)
       db.session.commit()
       return redirect(url_for('routes.view_question', id=id))
   return render_template('question.html', question=question)

@bp.route('/logout')
@login_required
def signout():
   logout_user()
   return redirect(url_for('routes.index'))

@bp.route('/ask', methods=['GET', 'POST'])
@login_required
def create_question():
   if request.method == 'POST':
       question = Question(title=request.form['title'],
                         content=request.form['content'],
                         author=current_user)
       db.session.add(question)
       db.session.commit()
       return redirect(url_for('routes.index'))
   return render_template('ask.html')
