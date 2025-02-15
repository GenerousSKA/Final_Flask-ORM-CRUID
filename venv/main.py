from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    borrowed_books = db.relationship('Borrow', backref='user', lazy=True)

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    books = db.relationship('Book', backref='author', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)
    borrows = db.relationship('Borrow', backref='book', lazy=True)

class Borrow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

def validate_json(data, required_fields):
    for field in required_fields:
        if field not in data:
            return False
    return True

@app.route('/users/', methods=['GET', 'POST'])
def users():
    if request.method == 'GET':
        users = User.query.all()
        users_list = [{'id': user.id, 'name': user.name, 'email': user.email} for user in users]
        return jsonify(users_list)
    
    elif request.method == 'POST':
        data = request.get_json()
        if not validate_json(data, ['name', 'email']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        new_user = User(name=data['name'], email=data['email'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'id': new_user.id, 'name': new_user.name, 'email': new_user.email}), 201

@app.route('/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
def user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'GET':
        return jsonify({'id': user.id, 'name': user.name, 'email': user.email})
    
    elif request.method == 'PUT':
        data = request.get_json()
        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            user.email = data['email']
        db.session.commit()
        return jsonify({'id': user.id, 'name': user.name, 'email': user.email})
    
    elif request.method == 'DELETE':
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})

@app.route('/books/', methods=['GET', 'POST'])
def books():
    if request.method == 'GET':
        books = Book.query.all()
        books_list = [{'id': book.id, 'title': book.title, 'author_id': book.author_id} for book in books]
        return jsonify(books_list)
    
    elif request.method == 'POST':
        data = request.get_json()
        if not validate_json(data, ['title', 'author_id']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        new_book = Book(title=data['title'], author_id=data['author_id'])
        db.session.add(new_book)
        db.session.commit()
        return jsonify({'id': new_book.id, 'title': new_book.title, 'author_id': new_book.author_id}), 201

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return jsonify({'message': 'Book deleted successfully'})

@app.route('/books/author/<int:author_id>', methods=['GET'])
def books_by_author(author_id):
    books = Book.query.filter_by(author_id=author_id).all()
    books_list = [{'id': book.id, 'title': book.title} for book in books]
    return jsonify(books_list)

@app.route('/authors/', methods=['GET', 'POST'])
def authors():
    if request.method == 'GET':
        authors = Author.query.all()
        authors_list = [{'id': author.id, 'name': author.name} for author in authors]
        return jsonify(authors_list)
    
    elif request.method == 'POST':
        data = request.get_json()
        if not validate_json(data, ['name']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        new_author = Author(name=data['name'])
        db.session.add(new_author)
        db.session.commit()
        return jsonify({'id': new_author.id, 'name': new_author.name}), 201

@app.route('/authors/<int:author_id>/books', methods=['GET'])
def author_books(author_id):
    author = Author.query.get_or_404(author_id)
    books_list = [{'id': book.id, 'title': book.title} for book in author.books]
    return jsonify(books_list)

@app.route('/borrow/', methods=['POST'])
def borrow_book():
    data = request.get_json()
    if not validate_json(data, ['user_id', 'book_id']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    new_borrow = Borrow(user_id=data['user_id'], book_id=data['book_id'])
    db.session.add(new_borrow)
    db.session.commit()
    return jsonify({'id': new_borrow.id, 'user_id': new_borrow.user_id, 'book_id': new_borrow.book_id, 'borrow_date': new_borrow.borrow_date}), 201

@app.route('/users/<int:user_id>/borrowed_books', methods=['GET'])
def user_borrowed_books(user_id):
    user = User.query.get_or_404(user_id)
    borrowed_books = [{'id': borrow.book.id, 'title': borrow.book.title, 'borrow_date': borrow.borrow_date} for borrow in user.borrowed_books]
    return jsonify(borrowed_books)

@app.route('/books/<int:book_id>/borrowers', methods=['GET'])
def book_borrowers(book_id):
    book = Book.query.get_or_404(book_id)
    borrowers = [{'id': borrow.user.id, 'name': borrow.user.name, 'borrow_date': borrow.borrow_date} for borrow in book.borrows]
    return jsonify(borrowers)

if __name__ == '__main__':
    app.run(debug=True)