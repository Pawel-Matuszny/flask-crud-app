from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://233dada331c140fb971a819e5a05bd71@o933564.ingest.sentry.io/5882670",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)

import os

env_username = os.environ['DB_USER']
env_password = os.environ['DB_PASS']
env_host = os.environ['DB_HOST']
env_db_name = os.environ['DB_NAME']
env_port = os.environ['DB_PORT']

app = Flask(__name__)

sql_url ='postgresql+psycopg2://%s:%s@%s:%s/%s?sslmode=prefer&sslrootcert=/app/docker/ssl/server-ca.pem&sslcert=/app/docker/ssl/client-cert.pem&sslkey=/app/docker/ssl/client-key.pem' % (env_username, env_password, env_host, env_port, env_db_name)

app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = sql_url

db = SQLAlchemy(app)
migrate = Migrate(app, db,compare_type=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(100))
    admin = db.Column(db.Boolean)

class Articles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    is_finished = db.Column(db.Boolean)
    user_public_id = db.Column(db.String(50))

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        
        if not token:
            return jsonify({'message' : 'Token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message' : 'Token is invalid'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


@app.route("/user", methods=['POST'])
@token_required
def create_user(current_user):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function'})

    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(public_id=str(uuid.uuid4()), name=data['name'], password=hashed_password, admin=False)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message' : 'New user created'})


@app.route('/user/<public_id>', methods=['PUT'])
@token_required
def promote_user(public_id, current_user):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message' : 'No user found'})

    user.admin = True
    db.session.commit()
    
    return jsonify({'mesage' : 'The user has been promoted'})

@app.route('/user/<public_id>', methods=['GET'])
@token_required
def get_one_user(public_id, current_user):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message' : 'No user found'})

    user_data = {}
    user_data['public_id'] = user.public_id
    user_data['name'] = user.name
    user_data['password'] = user.password
    user_data['admin'] = user.admin
    
    return jsonify({'user' : user_data})

@app.route('/user', methods=['GET'])
@token_required
def get_all_users(current_user):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function'})

    users = User.query.all()

    output = []

    for user in users:
        user_data = {}
        user_data['public_id'] = user.public_id
        user_data['name'] = user.name
        user_data['password'] = user.password
        user_data['admin'] = user.admin
        output.append(user_data)
    
    return jsonify({'users' : output})

@app.route('/user/<public_id>', methods=['DELETE'])
@token_required
def delete_user(public_id, current_user):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message' : 'No user found'})

    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'mesage' : 'The user has been deleted'})

@app.route('/article', methods=['GET'])
@token_required
def get_all_articles(current_user):
    articles = Articles.query.filter_by(user_public_id=current_user.public_id).all()

    output = []

    for article in articles:
        article_data = {}
        article_data['id'] = article.id
        article_data['text'] = article.text
        article_data['is_finished'] = article.is_finished
        article_data['date_created'] = article.date_created
        output.append(article_data)

    return jsonify({'articles' : output})

@app.route('/article/<article_id>', methods=['GET'])
@token_required
def get_one_article(current_user, article_id):
    article = Articles.query.filter_by(id=article_id, user_public_id=current_user.public_id).first()

    if not article:
        return jsonify({'message' : 'No article found'})

    article_data = {}
    article_data['id'] = article.id
    article_data['text'] = article.text
    article_data['is_finished'] = article.is_finished
    article_data['date_created'] = article.date_created

    return jsonify(article_data)

@app.route('/article', methods=['POST'])
@token_required
def create_article(current_user):
    data = request.get_json()

    new_article = Articles(text=data['text'], is_finished=False, user_public_id=current_user.public_id)
    db.session.add(new_article)
    db.session.commit()

    return jsonify({'message' : "Article created"})

@app.route('/article/<article_id>', methods=['PUT'])
@token_required
def finish_article(current_user, article_id):
    article = Articles.query.filter_by(id=article_id, user_public_id=current_user.public_id).first()

    if not article:
        return jsonify({'message' : 'No article found'})

    article.is_finished = True
    db.session.commit()

    return jsonify({'message' : 'Article has been finished'})

@app.route('/article/<article_id>', methods=['DELETE'])
@token_required
def delete_article(current_user, article_id):
    article = Articles.query.filter_by(id=article_id, user_public_id=current_user.public_id).first()

    if not article:
        return jsonify({'message' : 'No article found'})

    db.session.delete(article)
    db.session.commit()

    return jsonify({'message' : 'Article has been deleted'})

@app.route('/login')
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    user = User.query.filter_by(name=auth.username).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})
    
    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'public_id' : user.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=int(os.environ['TOKEN_EXPIRATION_TIME_IN_MINUTES']))}, app.config['SECRET_KEY'])

        return jsonify({'token' : token.decode('UTF-8')})

    return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

@app.route('/status')
def health_check():
    try:
        conn = db.engine.connect()
        conn.close()
    except Exception as e:
        return jsonify({'database_status' : 'offline'})

    return jsonify({'database_status' : 'online'})


@app.route('/http-health')
def http_health():
    return "OK"

if __name__ == "__main__":
    app.run()