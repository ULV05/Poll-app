import os
import signal
import sys
from datetime import datetime
from typing import Any
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

DEBUG = True
HOST = 'localhost'
PORT = 5000

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///polls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    questions = db.relationship('Question', backref='poll', lazy=True, cascade="all, delete-orphan")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    multiple = db.Column(db.Boolean, default=False)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    options = db.relationship('Option', backref='question', lazy=True, cascade="all, delete-orphan")

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False)
    votes = db.Column(db.Integer, default=0)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

def get_poll_or_404(poll_id: int) -> Poll:
    poll = Poll.query.get(poll_id)
    if not poll:
        abort(404, description="Опрос не найден")
    return poll

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/take_poll')
def take_poll():
    poll_id = request.args.get('poll_id')
    if poll_id:
        return redirect(url_for('poll', poll_id=poll_id))
    return render_template('take_poll.html')

@app.route('/poll')
def poll_redirect():
    poll_id = request.args.get('id')
    if poll_id:
        return redirect(url_for('poll', poll_id=poll_id))
    return redirect(url_for('take_poll'))

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        new_poll = Poll(
            title=request.form.get('title', '').strip(),
            author=request.form.get('author', '').strip()
        )
        
        question_counter = 1
        while f'question_{question_counter}_text' in request.form:
            question_text = request.form.get(f'question_{question_counter}_text', '').strip()
            if question_text:
                question = Question(
                    text=question_text,
                    multiple=f'question_{question_counter}_multiple' in request.form,
                    poll=new_poll
                )
                
                option_counter = 1
                while f'question_{question_counter}_option_{option_counter}' in request.form:
                    opt_text = request.form[f'question_{question_counter}_option_{option_counter}'].strip()
                    if opt_text:
                        question.options.append(Option(text=opt_text))
                    option_counter += 1
                
                db.session.add(question)
            question_counter += 1
        
        db.session.add(new_poll)
        db.session.commit()
        
        return render_template(
            'created.html',
            poll_id=new_poll.id,
            poll_link=url_for('poll', poll_id=new_poll.id, _external=True),
            results_link=url_for('results', poll_id=new_poll.id, _external=True)
        )
    
    return render_template('create.html')

@app.route('/poll/<int:poll_id>')
def poll(poll_id: int):
    poll = get_poll_or_404(poll_id)
    
    if not poll.questions:
        abort(404, description="В опросе нет вопросов")
    
    questions_data = []
    for question in poll.questions:
        if not question.options:
            continue  
            
        questions_data.append({
            'id': question.id,
            'text': question.text,
            'multiple': question.multiple,
            'options': {opt.id: {'text': opt.text, 'votes': opt.votes} for opt in question.options}
        })
    
    if not questions_data:
        abort(404, description="В опросе нет вопросов с вариантами ответа")
    
    poll_data = {
        'id': poll.id,
        'title': poll.title,
        'author': poll.author,
        'questions': questions_data
    }
    
    return render_template('poll.html', poll=poll_data)

@app.route('/submit/<int:poll_id>', methods=['POST'])
def submit(poll_id: int):
    poll = get_poll_or_404(poll_id)
    
    try:
        for question in poll.questions:
            if question.multiple:
                selected_options = request.form.getlist(f'question_{question.id}_options')
            else:
                selected_options = [request.form[f'question_{question.id}_option']]
            
            for option_id in selected_options:
                option = next((opt for opt in question.options if opt.id == int(option_id)), None)
                if option:
                    option.votes += 1
        
        db.session.commit()
    
    except (KeyError, ValueError):
        abort(400, description="Неверные данные формы")
    
    return redirect(url_for('results', poll_id=poll_id))

@app.route('/results/<int:poll_id>')
def results(poll_id: int):
    poll = get_poll_or_404(poll_id)
    
    questions_data = []
    total_votes = 0
    
    for question in poll.questions:
        question_votes = sum(opt.votes for opt in question.options)
        total_votes += question_votes
        
        options = []
        for opt in question.options:
            percent = round((opt.votes / question_votes) * 100, 1) if question_votes > 0 else 0.0
            options.append({
                'id': opt.id,
                'text': opt.text,
                'votes': opt.votes,
                'percent': percent
            })
        
        questions_data.append({
            'id': question.id,
            'text': question.text,
            'multiple': question.multiple,
            'options': options,
            'total_votes': question_votes
        })
    
    return render_template(
        'results.html',
        poll={
            'id': poll.id,
            'title': poll.title,
            'author': poll.author
        },
        questions=questions_data,
        total_votes=total_votes
    )

@app.route('/view_results', methods=['GET', 'POST'])
def view_results():
    if request.method == 'POST':
        poll_id = int(request.form.get('poll_id', 0))
        return redirect(url_for('results', poll_id=poll_id))
    return render_template('view_results.html')

def shutdown_handler(signum: int, frame: any) -> None:
    print("\nСервер останавливается...")
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    with app.app_context():
        db.create_all()
    
    print(f"Сервер запущен на http://{HOST}:{PORT}")
    print("Нажмите Ctrl+C для остановки")
    app.run(debug=DEBUG, host=HOST, port=PORT)