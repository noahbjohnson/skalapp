from app import app, db
from app.models import User, Post, Comment, Like
import random
import lipsum

def wipeDB():
    User.query.delete()
    Post.query.delete()
    Comment.query.delete()
    Like.query.delete()
    db.session.commit()

def deleteOrphans():
    comments = Comment.query.filter_by(user_id=None).all()
    posts = Post.query.filter_by(user_id=None).all()
    likes = Like.query.filter_by(user_id=None).all()

    for field in [comments, posts, likes]:
        for row in field:
            db.session.delete(row)
    db.session.commit()

def createUsers():
    names = ['Abigail', 'Alice', 'Amber', 'Amelia', 'Amy', 'Ava', 'Brooke',
		'Caitlin', 'Charlotte', 'Chloe', 'Daisy', 'Elizabeth', 'Ella', 'Ellie',
		'Emily', 'Emma', 'Erin', 'Eva', 'Evie', 'Freya', 'Grace', 'Hannah',
		'Holly', 'Imogen', 'Isabel', 'Isabella', 'Isabelle', 'Isla', 'Jasmine',
		'Jessica', 'Katie', 'Keira', 'Leah', 'Lilly', 'Lily', 'Lola', 'Lucy',
		'Matilda', 'Megan', 'Mia', 'Millie', 'Molly', 'Olivia', 'Phoebe',
		'Poppy', 'Ruby', 'Scarlett', 'Sophia', 'Sophie', 'Summer', 'Adam',
		'Alex', 'Alexander', 'Alfie', 'Archie', 'Benjamin', 'Callum',
		'Cameron', 'Charlie', 'Connor', 'Daniel', 'Dylan', 'Edward', 'Ethan',
		'Finley', 'George', 'Harrison', 'Harry', 'Harvey', 'Henry', 'Isaac',
		'Jack', 'Jacob', 'Jake', 'James', 'Jayden', 'Joseph', 'Joshua', 'Leo',
		'Lewis', 'Liam', 'Logan', 'Lucas', 'Luke', 'Matthew', 'Max',
		'Mohammed', 'Muhammad', 'Nathan', 'Noah', 'Oliver', 'Oscar', 'Owen',
		'Rhys', 'Riley', 'Ryan', 'Samuel', 'Thomas', 'Tyler', 'William',]
    for name in names:
        u = User()
        if User.query.filter_by(username=name).first():
            u.username = name + str(random.randint(0,99))
        else:
            u.username = name
        u.email = u.username.lower() + '@luther.edu'
        u.avatar = random.choice(['helmet.png', 'axe.png', 'ship.png'])
        u.set_password('password')
        aboutlen = random.randint(0,23)
        aboutme = lipsum.generate_words(aboutlen)
        u.about_me = aboutme
        db.session.add(u)

    db.session.commit()


def createPosts(postsPerUser=5):
    users = User.query.all()
    for user in users:
        for i in range(postsPerUser):
            bodyLen = random.randint(4,81)
            bodyText = lipsum.generate_words(bodyLen)
            p = Post(user_id=user.id, body=bodyText)
            db.session.add(p)
    db.session.commit()


def createFollows(usersToFollow=5):
    users = User.query.all()
    for user in users:
        for i in range(usersToFollow):
            tofollow = random.choice(users)
            if tofollow == user:
                print('oops')
            else:
                user.follow(tofollow)
    db.session.commit()


def createComments(commentsPerUser=5):
    users = User.query.all()
    posts = Post.query.all()
    for user in users:
        for i in range(commentsPerUser):
            bodylen = random.randint(0, 23)
            body = lipsum.generate_words(bodylen)
            post = random.choice(posts)
            user.create_comment(post, body)
    db.session.commit()


def likePosts(postsToLike=5):
    users = User.query.all()
    posts = Post.query.all()
    for user in users:
        if posts:
            for post in range(postsToLike):
                user.like(random.choice(posts))
    db.session.commit()


def likeComments(commentsToLike=5):
    users = User.query.all()
    comments = Comment.query.all()
    for user in users:
        if comments:
            for i in range(commentsToLike):
                user.like_comment(random.choice(comments))
    db.session.commit()


