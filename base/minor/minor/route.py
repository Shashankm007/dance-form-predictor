from werkzeug.utils import secure_filename
from flask import render_template, url_for, flash, redirect, request, Response, current_app
from minor import app, mail, db
from minor.forms import (
    RegistrationForm, LoginForm, ResetForm, PasswordForm, PostForm)
from minor.models import User, Post
from flask_mail import Message
import bcrypt
import os
from flask_login import login_user, current_user, logout_user, login_required
from minor.camera import VideoCamera
from collections import Counter

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mkv', 'mp4'}

UPLOAD_FOLDER = './uploads'


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(fullname=form.name.data, email=form.email.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.confirmation_token()
        send_confirmation(token)
        flash(f'confirmation mail is send to the email account')
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and form.password.data == user.password:
            login_user(user, remember=form.remember.data)
            flash('Successfully logged in!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Unsuccessful login check email or password!', 'danger')
    return render_template('login.html', form=form)


@app.route("/confirmation/<token>", methods=['GET', 'POST'])
def reset_token(token):
    user = User.verify_confirmation_token(token)
    if user is None:
        flash('Invalid or expired token', 'warning')
    user.confirm = 1
    db.session.commit()
    flash(f'Account Verified Successfully!', 'success')
    return redirect(url_for('login'))


def send_confirmation(token):
    msg = Message('localhost:5000/confirmation/{}'.format(token),
                  recipients=['godiyalanu@gmail.com'])
    mail.send(msg)
    return None


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/resetpassword', methods=['GET', 'POST'])
def reset_password():
    form = ResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash('No account is registered with that email id', 'warning')
        else:
            token = user.confirmation_token()
            send_forget_password(token)
            flash('Email is sent to registered mail for further instruction!', 'info')
            return redirect(url_for('home'))

    return render_template('resetpassword.html', form=form)


@app.route("/resetpassword/<token>", methods=['GET', 'POST'])
def forget_token(token):
    user = User.verify_confirmation_token(token)
    if user is None:
        flash('Invalid or expired token', 'warning')
        return redirect(url_for('login'))
    form = PasswordForm()
    if form.validate_on_submit():
        user.password = form.password.data
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('password.html', form=form)


def send_forget_password(token):
    msg = Message('localhost:5000/resetpassword/{}'.format(token),
                  recipients=['godiyalanu@gmail.com'])
    mail.send(msg)
    return None


@app.route("/posts/newpost", methods=['GET', 'POST'])
@login_required
def newpost():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data,
                    content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your Post has been Created!', 'success')
        return redirect(url_for('home'))
    return render_template('new_post.html', form=form)


@app.route("/check", methods=['GET', 'POST'])
@login_required
def check():
    return render_template('check.html')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            print(filename)
            return redirect(url_for('video_feed', filename=filename))
    return render_template('upload.html')


def gen(camera, frames):
    x = True
    while x == True:
        # print(frames)
        frame, prediction = camera.get_frame(frames)
        # print(len(prediction))
        out = frames-5
        if(len(prediction) > out):
            c = Counter(prediction)
            Keymax = max(c, key=c.get)
            print(Keymax)
            x = False
        # print(frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


# frames = VideoCamera(request.args['filename']).count_frames_manual()


@app.route('/video_feed', methods=['GET', 'POST'])
#@login_required
def video_feed():
    frames = VideoCamera(request.args['filename']).count_frames_manual()
    # return redirect('/', code=302, Response=Response(gen(VideoCamera(request.args['filename']), frames), mimetype='multipart/x-mixed-replace; boundary=frame'))
    return Response(gen(VideoCamera(request.args['filename']), frames), mimetype='multipart/x-mixed-replace; boundary=frame')
