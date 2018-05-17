from flask import render_template, flash, redirect, url_for, request
from app import app, db, limiter
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, CommentForm, ResetPasswordRequestForm, ResetPasswordForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post, Comment
from werkzeug.urls import url_parse
from datetime import datetime
from app.webmail import send_password_reset_email, send_verification_email

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@limiter.request_filter
def whitelist_get():
    return request.method == "GET"


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
@login_required
@limiter.limit("5 per hour", key_func=lambda: current_user.id)
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
       if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
       if posts.has_prev else None
    return render_template('index.html', title='Home', form=form, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("100 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        send_verification_email(user)
        flash('Please check your inbox for a confirmation email.')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
@limiter.limit("5 per hour", key_func=lambda: current_user.username)
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        if current_user.username != form.username.data:
            current_user.old_username = current_user.username
            current_user.changed_username()
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        current_user.enable_last_seen = form.enable_last_seen.data
        current_user.avatar = form.avatar.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.avatar.data = current_user.avatar
        form.about_me.data = current_user.about_me
        form.enable_last_seen.data = current_user.enable_last_seen
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/follow/<username>')
@login_required
@limiter.limit("20 per hour", key_func=lambda: current_user.username)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
@limiter.limit("20 per hour", key_func=lambda: current_user.username)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('user', username=username))

@app.route('/newest')
@login_required
def newest():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('newest', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('newest', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Newest', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)

@app.route('/like/<post_id>', methods=['GET', 'POST'])
@login_required
@limiter.limit("50 per hour", key_func=lambda: current_user.username)
def like(post_id):
    current_user.like(Post.query.get(post_id))
    flash("post liked!")
    current_user.update_stats()
    Post.query.get(post_id).author.update_stats()
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/unlike/<post_id>', methods=['GET', 'POST'])
@login_required
def unlike(post_id):
    current_user.unlike(Post.query.get(post_id))
    current_user.update_stats()
    Post.query.get(post_id).author.update_stats()
    db.session.commit()
    flash("post unliked!")
    return redirect(url_for('index'))


@app.route('/postdetail/<post_id>', methods=['GET', 'POST'])
@login_required
@limiter.limit("20 per hour", key_func=lambda: current_user.username)
def postdetail(post_id):
    form = CommentForm()
    if form.validate_on_submit():
        c = Comment(user_id=current_user.id, post_id=post_id, body=form.comment.data)
        db.session.add(c)
        db.session.commit()
        flash('Your comment has been posted.')
        return redirect(url_for('postdetail', post_id=post_id))
    return render_template('post_detail.html', title='Post View',
                           form=form, post=Post.query.get(post_id))


@app.route('/reset_password_request', methods=['GET', 'POST'])
@limiter.limit("20 per hour")
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
@limiter.limit("20 per hour")
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/verify/<token>', methods=['GET', 'POST'])
@limiter.limit("20 per hour")
def verify(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_verify_token(token)
    if user:
        flash('Account verified!')
        user.verified = True
        db.session.commit()
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

@app.route('/verify_request', methods=['GET', 'POST'])
@limiter.limit("20 per hour")
def verify_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_verification_email(user)
        flash('Check your email for the instructions to verify your account')
        return redirect(url_for('login'))
    return render_template('verify_request.html',
                           title='Reset Password', form=form)
