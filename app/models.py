from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db, login, app
from flask_login import UserMixin
from time import time
import jwt


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    avatar = db.Column(db.String(24), default="helmet.png")
    clout = db.Column(db.Integer, index=True, default=0)
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    enable_last_seen = db.Column(db.Boolean, default=True)
    old_username = db.Column(db.String(64))
    username_last_changed = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    verified = db.Column(db.Boolean, default=False)
    likes = db.relationship('Like', backref='author', lazy='dynamic')
    post_count = db.Column(db.Integer, index=True, default=0)
    banned = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_avatar(self, avatar):
        self.avatar = avatar

    def get_avatar(self):
        return '/static/avatars/' + self.avatar

    def changed_username(self):
        self.username_last_changed = datetime.utcnow()

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
            followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def likes_post(self, post):
        return Like.query.filter_by(user_id=self.id).filter_by(post_id=post.id).first() is not None

    def like(self, post):
        if not self.likes_post(post):
            db.session.add(Like(user_id=self.id, post_id=post.id))

    def unlike(self, post):
        if self.likes_post(post):
            db.session.delete(Like.query.filter_by(user_id=self.id).filter_by(post_id=post.id).first())

    def likes_comment(self, comment):
        return Like.query.filter_by(user_id=self.id).filter_by(comment_id=comment.id).first() is not None

    def like_comment(self, comment):
        if not self.likes_comment(comment):
            db.session.add(Like(user_id=self.id, comment_id=comment.id))

    def unlike_comment(self, comment):
        if self.like_comment(comment):
            db.session.delete(Like.query.filter_by(user_id=self.id).filter_by(comment_id=comment.id).first())

    def update_stats(self):
        post_list = Post.query.filter_by(user_id=self.id).all()
        comment_list = Comment.query.filter_by(user_id=self.id).all()

        posts = len(post_list)
        clout = 0

        for post in post_list:
            clout += post.get_like_count()

        for comment in comment_list:
            clout += comment.get_like_count()

        self.post_count = posts
        self.clout = clout

    def ban(self):
        self.banned = True

    def unban(self):
        self.banned = False

    def create_comment(self, post, body):
        c = Comment()
        c.post_id = post.id
        c.body = body
        c.user_id = self.id
        db.session.add(c)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def get_verify_token(self, expires_in=60000):
        return jwt.encode(
            {'verify': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_verify_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['verify']
        except:
            return
        return User.query.get(id)



class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(1400))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    likes = db.relationship('Like', backref='post', lazy='dynamic')

    def __repr__(self):
        return '<Post: {}...>'.format(self.body[:50])

    def get_comments(self):
        return Comment.query.filter_by(post_id=self.id).order_by(Comment.timestamp.asc())

    def get_comment_count(self):
        return len(Comment.query.filter_by(post_id=self.id).all())

    def get_comment_id(self):
        return "#" + str(self.id)

    def get_like_count(self):
        return len(Like.query.filter_by(post_id=self.id).all())


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), index=True)
    likes = db.relationship('Like', backref='comment', lazy='dynamic')

    def __repr__(self):
        return '<Comment: {}>'.format(self.body)

    def get_like_count(self):
        return len(Like.query.filter_by(comment_id=self.id).all())


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), index=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), index=True)

    def __repr__(self):
        if self.post_id:
            value = "post " + str(self.post_id)
        else:
            value = "comment " + str(self.comment_id)
        return '<User number {} likes: {}>'.format(self.user_id, value)

# TODO: add email confirmation system
