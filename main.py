from crypt import methods
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

##Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Board(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    tasks = db.relationship("BoardTasks", back_populates="board")
    
    def to_dict(self):
        return { column.name : getattr(self, column.name) for column in self.__table__.columns }

class BoardTasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    summary = db.Column(db.String(500), nullable=False)
    assignee = db.Column(db.String(250))
    state = db.Column(db.String(250), nullable=False)
    board = db.relationship("Board", back_populates="tasks")
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'))

    def to_dict(self):
        return { column.name : getattr(self, column.name) for column in self.__table__.columns }
db.create_all()

class TaskForm(FlaskForm):
    summary = StringField('Task Summary', validators=[DataRequired()])
    assignee = StringField('Assignee', validators=[DataRequired()])
    submit = SubmitField('Submit')

# Flask routes
@app.route("/")
def home():
    # Page displaying all Board cards
    all_team_boards = get_all_boards()
    return render_template("index.html", boards = all_team_boards)

@app.route('/board/<int:board_id>')
def get_board(board_id):
    board = get_board_by_id(board_id)
    return render_template('board.html', board=board)

@app.route('/add-board', methods=['GET', 'POST'])
def create_new_board():
    create_board(title=request.values['board_title'])
    all_team_boards = get_all_boards()
    return render_template("index.html", boards = all_team_boards)

@app.route('/add-task/<int:board_id>', methods=['GET', 'POST'])
def add_task(board_id):
    create_tasks(board_id=board_id, summary=request.values['summary'], assignee=request.values['assignee'])
    return redirect(url_for('get_board', board_id=board_id))

@app.route('/update-board-summary/<int:board_id>')
def update_board_info(board_id):
    board_title = request.args.title
    update_board_summary(board_id=board_id, summary=board_title)
    return redirect(url_for('home'))

@app.route('/update-task/<int:task_id>', methods=['GET', 'POST'])
def update_task(task_id):
    form = TaskForm()
    task = get_task_by_id(task_id)
    if request.method == "GET":
        form.assignee.data = task.assignee
        form.summary.data = task.summary

    if form.validate_on_submit():
        update_task(task_id=task_id ,assignee = form.assignee.data)
        return redirect(url_for('get_board', board_id=task.board_id))
    return render_template('add_and_update.html', title="Update Task", form=form)

@app.route('/update_task_state')
def update_task_state():
    if request.values['current_state'] == 'Backlog':
        state = 'In Progress'
    else:
        state = 'Done'
    update_task(task_id=request.values['task_id'], state=state)
    return redirect(url_for('get_board', board_id=request.values['board_id']))

@app.route('/delete_task/<int:task_id>')
def delete_board_task(task_id):
    delete_task(task_id)
    board_id = request.values['board_id']
    return redirect(url_for('get_board', board_id=board_id))

@app.route('/delete_board/<int:board_id>')
def delete_board(board_id):
    delete_board(board_id)
    return redirect(url_for('home'))

# board task methods
def create_tasks(board_id, summary, assignee):
    task =  BoardTasks(summary=summary, assignee=assignee, state="Backlog", board_id=board_id)
    db.session.add(task)
    db.session.commit()

def update_task(task_id, state, assignee=None):
    task =  BoardTasks.query.filter_by(id=task_id).first()
    if assignee is not None:
        task.assignee = assignee
    if state is not None:
        task.state = state
    db.session.commit()

def delete_task(task_id):
    task =  BoardTasks.query.get(task_id)
    db.session.delete(task)
    db.session.commit()

def get_all_board_tasks(board_id):
    tasks =  BoardTasks.query.filter_by(board_id=board_id).all()
    task_list = [task.to_dict() for task in tasks]
    return task_list

def get_task_by_id(task_id):
    task =  BoardTasks.query.filter_by(id=task_id).first().to_dict()
    return task

# board methods
def create_board(title):
        board =  Board(title=title)
        db.session.add(board)
        db.session.commit()

def update_board_summary(board_id, summary):
    board =  Board.query.filter_by(id=board_id).first()
    if summary is not None:
        board.summary = summary
        db.session.commit()

def delete_board(board_id):
    board =  Board.query.get(board_id)
    db.session.delete(board)
    db.session.commit()

def get_all_boards():
    boards =  Board.query.all()
    board_list = [board.to_dict() for board in boards]
    return board_list

def get_board_by_id(board_id):
    board =  Board.query.filter_by(id=board_id).first().to_dict()
    tasks = get_all_board_tasks(board_id=board_id)
    board["tasks"] = tasks
    return board

if __name__ == '__main__':
    app.run(debug=True)