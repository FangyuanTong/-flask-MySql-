import os
from flask import Flask, render_template, redirect, url_for, abort, request, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql

app = Flask(__name__)

# 数据库配置（默认使用 root:123456@localhost/new_student），可通过环境变量覆盖
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASS = os.environ.get('DB_PASS', '123456')
DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_NAME = os.environ.get('DB_NAME', 'new_student')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 用于 session 的 secret key（可通过环境变量覆盖）
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-secret-for-dev')


class EmploymentQuestion(db.Model):
    __tablename__ = 'employment_questions'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)


class StudyQuestion(db.Model):
    __tablename__ = 'study_questions'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)


class DailyQuestion(db.Model):
    __tablename__ = 'daily_questions'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)


class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    title = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


def seed_if_needed():
    # 在表为空时插入示例数据
    if not EmploymentQuestion.query.first():
        items = [
            ('how', '如何就业', '<p>投递简历、面试准备与职业定位建议。</p>'),
            ('intern', '怎么找实习', '<p>实习渠道与简历投递小技巧。</p>'),
            ('experience', '学长学姐经验', '<p>往届学长学姐的经验分享与建议。</p>'),
        ]
        for slug, title, content in items:
            db.session.add(EmploymentQuestion(slug=slug, title=title, content=content))

    if not StudyQuestion.query.first():
        items = [
            ('correct', '正确学习', '<p>基础打牢与系统性学习方法。</p>'),
            ('efficient', '高效学习', '<p>时间规划、专注技巧与复习策略。</p>'),
            ('experience', '学长学姐经验', '<p>课程选择与学习资源推荐。</p>'),
        ]
        for slug, title, content in items:
            db.session.add(StudyQuestion(slug=slug, title=title, content=content))

    if not DailyQuestion.query.first():
        items = [
            ('school', '学校问题', '<p>校园常见问题与解答。</p>'),
            ('resources', '高效利用学校资源', '<p>图书馆、实验室、导师沟通等资源利用建议。</p>'),
            ('experience', '学长经验', '<p>生活小技巧与校园适应经验。</p>'),
        ]
        for slug, title, content in items:
            db.session.add(DailyQuestion(slug=slug, title=title, content=content))

    db.session.commit()


def initialize_database():
    # 确保数据库存在（如果 MySQL 服务可达）
    try:
        conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, charset='utf8mb4')
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.commit()
        conn.close()
    except Exception as e:
        app.logger.warning('未能自动创建数据库（请确保 MySQL 可用或手动创建数据库 new_student）：%s', e)

    # 在应用上下文中创建表并插入示例数据
    try:
        with app.app_context():
            db.create_all()
            seed_if_needed()
            # 确保 users 表存在（不会覆盖已有用户）
            # 如果没有用户，可创建一个示例用户（可选）
            if not User.query.first():
                u = User(username='admin')
                u.set_password('admin')
                db.session.add(u)
                db.session.commit()
    except Exception as e:
        app.logger.error('初始化数据库时出错：%s', e)


@app.route('/')
def index():
    # 默认跳转到就业 -> 如何就业 子页面
    return redirect(url_for('subpage', main='employment', sub='how'))


@app.route('/<main>/<sub>')
def subpage(main, sub):
    # 从数据库读取对应板块和 slug
    model_map = {
        'employment': EmploymentQuestion,
        'study': StudyQuestion,
        'daily': DailyQuestion,
    }

    if main not in model_map:
        abort(404)

    model = model_map[main]
    item = model.query.filter_by(slug=sub).first()
    if not item:
        abort(404)

    return render_template('subpage.html', current_main=main, current_sub=sub, title=item.title, content_html=item.content)


@app.route('/submit')
def submit():
    return render_template('submit.html', current_main='submit', current_sub='')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('用户名和密码为必填项')
            return render_template('register.html', current_main='', current_sub='')
        # 检查重复用户名
        if User.query.filter_by(username=username).first():
            flash('用户名已存在，请换一个')
            return render_template('register.html', current_main='', current_sub='')
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        # 登录
        session['user_id'] = user.id
        session['username'] = user.username
        flash('注册成功，已登录')
        return redirect(url_for('index'))
    return render_template('register.html', current_main='', current_sub='')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('用户名或密码错误')
            return render_template('login.html', current_main='', current_sub='')
        session['user_id'] = user.id
        session['username'] = user.username
        flash('登录成功')
        return redirect(url_for('index'))
    return render_template('login.html', current_main='', current_sub='')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('已注销')
    return redirect(url_for('index'))


### API endpoints for submissions ###
@app.route('/api/submissions', methods=['GET', 'POST', 'DELETE'])
def api_submissions():
    if request.method == 'GET':
        subs = Submission.query.order_by(Submission.created_at.desc()).all()
        return jsonify([{
            'id': s.id,
            'name': s.name,
            'title': s.title,
            'message': s.message,
            'created_at': s.created_at.isoformat()
        } for s in subs])

    if request.method == 'POST':
        data = request.get_json() or request.form
        name = data.get('name')
        title = data.get('title')
        message = data.get('message')
        if not message:
            return jsonify({'error': 'message is required'}), 400
        s = Submission(name=name, title=title, message=message)
        db.session.add(s)
        db.session.commit()
        return jsonify({'id': s.id, 'created_at': s.created_at.isoformat()}), 201

    # DELETE -> 清空所有投稿（开发用）
    if request.method == 'DELETE':
        try:
            num = Submission.query.delete()
            db.session.commit()
            return jsonify({'deleted': num})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500


@app.route('/api/submissions/<int:sub_id>', methods=['DELETE'])
def api_delete_submission(sub_id):
    s = Submission.query.get(sub_id)
    if not s:
        return jsonify({'error': 'not found'}), 404
    try:
        db.session.delete(s)
        db.session.commit()
        return jsonify({'deleted': 1})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # 在启动前尝试初始化数据库
    initialize_database()
    # 开发时使用 debug=True；生产请通过 WSGI 服务器运行
    app.run(host='0.0.0.0', port=5000, debug=True)
