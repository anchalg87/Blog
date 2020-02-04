import os
import secrets
from PIL import Image
from myblog import app, db, bcrypt, mail
from flask import redirect, url_for, render_template, flash, request, abort
from myblog.forms import RegistrationForm, LoginForm, EditProfileForm, PostForm, DeletePostForm, ContactForm
from myblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message


@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', title='Home', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(firstname=form.firstname.data, lastname=form.lastname.data, username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/myprofile")
@login_required
def myprofile():
    user_image = url_for('static', filename='profile_pics/' + current_user.profile_pic)
    return render_template('profile.html', title='My Profile', user_image=user_image)


def save_image(user_image):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(user_image.filename)
    img_fn = random_hex + f_ext
    img_path = os.path.join(app.root_path, 'static/profile_pics', img_fn)

    output_size = (125, 125)
    i = Image.open(user_image).convert('RGB')
    i.thumbnail(output_size)
    i.save(img_path)

    return img_fn


@app.route("/editprofile", methods=['GET', 'POST'])
@login_required
def editprofile():
    form = EditProfileForm()
    if form.validate_on_submit():
        if form.user_img.data:
            image_file = save_image(form.user_img.data)
            current_user.profile_pic = image_file
        current_user.firstname = form.firstname.data
        current_user.lastname = form.lastname.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('myprofile'))
    elif request.method == 'GET':
        form.firstname.data = current_user.firstname
        form.lastname.data = current_user.lastname
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('editprofile.html', title='Edit Profile', form=form)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, post_content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('new_post.html', title='New Post',
                           form=form, legend='Create New Post')


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.post_content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('home'))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.post_content
    return render_template('new_post.html', title='Update Post',
                           form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['GET', 'POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = DeletePostForm()
    if form.validate_on_submit():
        db.session.delete(post)
        db.session.commit()
        flash('Your post has been deleted!', 'success')
        return redirect(url_for('home'))
    return render_template('delete_post.html', title='Delete Post', form=form)


@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)


@app.route("/contactus", methods=['GET', 'POST'])
def contactus():
    form = ContactForm()
    if form.validate_on_submit():
        from_email = form.from_email.data
        subject = form.subject.data
        message = form.message.data
        msg = Message(subject=subject,
                      sender=from_email,
                      recipients=["anchu.gupta@gmail.com"],
                      body=message)
        mail.send(msg)
        flash('Your message has been sent!', 'success')
        return redirect(url_for('home'))
    return render_template('contactus.html', title='Contact Us', form=form)
