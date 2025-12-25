from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import pymysql
from config import DB_CONFIG, SECRET_KEY, UPLOAD_FOLDER, MAX_BOOK_LOAN_DAYS, MAX_MAGAZINE_LOAN_DAYS
from models import db, User, Publication, BorrowRecord, Document
from utils import save_uploaded_file
import os
from datetime import datetime, timedelta

# 初始化Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# 配置数据库
app.config[
    'SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['db']}?charset=utf8mb4"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

# 初始化登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# 用户加载回调
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# 主页（重定向到登录页）
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('reader_dashboard'))
    return redirect(url_for('login'))


# 登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('登录成功！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('用户名或密码错误！', 'danger')

    return render_template('login.html')


# 注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('两次输入的密码不一致！', 'danger')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('用户名已存在！', 'danger')
            return render_template('register.html')

        # 创建新用户（默认读者角色）
        user = User(username=username, role='reader')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('注册成功，请登录！', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# 登出
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已成功登出！', 'success')
    return redirect(url_for('login'))


# ---------------- 管理员路由 ----------------
# 管理员仪表盘
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('权限不足！', 'danger')
        return redirect(url_for('index'))

    # 统计数据
    total_books = Publication.query.filter_by(type='book').count()
    total_magazines = Publication.query.filter_by(type='magazine').count()
    borrowed_count = Publication.query.filter_by(is_borrowed=True).count()
    overdue_count = Publication.query.filter(
        Publication.is_borrowed == True,
        Publication.due_date < datetime.utcnow()
    ).count()
    total_users = User.query.filter_by(role='reader').count()

    return render_template('admin/dashboard.html',
                           total_books=total_books,
                           total_magazines=total_magazines,
                           borrowed_count=borrowed_count,
                           overdue_count=overdue_count,
                           total_users=total_users)


# 管理出版物
@app.route('/admin/publications', methods=['GET', 'POST'])
@login_required
def manage_publications():
    if current_user.role != 'admin':
        flash('权限不足！', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # 添加出版物
        title = request.form['title']
        pub_type = request.form['type']
        author = request.form.get('author', '')
        isbn = request.form.get('isbn', '')
        category = request.form.get('category', '技术')
        issue = request.form.get('issue', '')
        publisher = request.form.get('publisher', '')

        # 检查ISBN是否重复（仅图书）
        if pub_type == 'book' and isbn and Publication.query.filter_by(isbn=isbn).first():
            flash('ISBN已存在！', 'danger')
            return redirect(url_for('manage_publications'))

        # 创建出版物
        publication = Publication(
            title=title,
            type=pub_type,
            author=author,
            isbn=isbn,
            category=category,
            issue=issue,
            publisher=publisher
        )
        db.session.add(publication)
        db.session.commit()
        flash('添加成功！', 'success')
        return redirect(url_for('manage_publications'))

    # 获取所有出版物
    publications = Publication.query.all()
    return render_template('admin/manage_publications.html', publications=publications)


# 删除出版物
@app.route('/admin/publications/delete/<int:pub_id>')
@login_required
def delete_publication(pub_id):
    if current_user.role != 'admin':
        flash('权限不足！', 'danger')
        return redirect(url_for('index'))

    pub = Publication.query.get_or_404(pub_id)
    db.session.delete(pub)
    db.session.commit()
    flash('删除成功！', 'success')
    return redirect(url_for('manage_publications'))


# 借阅统计
@app.route('/admin/statistics')
@login_required
def admin_statistics():
    if current_user.role != 'admin':
        flash('权限不足！', 'danger')
        return redirect(url_for('index'))

    # 按分类统计图书
    category_stats = db.session.query(
        Publication.category,
        db.func.count(Publication.id)
    ).filter_by(type='book').group_by(Publication.category).all()

    # 借阅次数统计（前10）
    borrow_stats = db.session.query(
        Publication.title,
        db.func.count(BorrowRecord.id)
    ).join(BorrowRecord).group_by(Publication.id).order_by(db.func.count(BorrowRecord.id).desc()).limit(10).all()

    # 逾期用户统计
    overdue_users = db.session.query(
        User.username,
        db.func.count(Publication.id)
    ).join(Publication, User.id == Publication.borrower_id).filter(
        Publication.is_borrowed == True,
        Publication.due_date < datetime.utcnow()
    ).group_by(User.id).all()

    return render_template('admin/statistics.html',
                           category_stats=category_stats,
                           borrow_stats=borrow_stats,
                           overdue_users=overdue_users)


# ---------------- 读者路由 ----------------
# 读者仪表盘
@app.route('/reader/dashboard')
@login_required
def reader_dashboard():
    if current_user.role != 'reader':
        flash('权限不足！', 'danger')
        return redirect(url_for('index'))

    # 我的借阅
    my_borrows = BorrowRecord.query.filter_by(
        user_id=current_user.id,
        status='borrowed'
    ).join(Publication).all()

    # 逾期数量
    overdue_count = sum(1 for br in my_borrows if br.publication.due_date < datetime.utcnow())

    return render_template('reader/dashboard.html',
                           my_borrows=my_borrows,
                           overdue_count=overdue_count)


# 借阅图书
@app.route('/reader/borrow')
@login_required
def borrow_books():
    if current_user.role != 'reader':
        flash('权限不足！', 'danger')
        return redirect(url_for('index'))

    # 搜索功能
    search = request.args.get('search', '')
    pub_type = request.args.get('type', 'all')

    query = Publication.query.filter_by(is_borrowed=False)
    if search:
        query = query.filter(Publication.title.like(f'%{search}%'))
    if pub_type != 'all':
        query = query.filter_by(type=pub_type)

    publications = query.all()
    return render_template('reader/borrow_books.html',
                           publications=publications,
                           search=search,
                           pub_type=pub_type)


# 执行借阅
# 借阅出版物
@app.route('/reader/borrow/<int:pub_id>')
@login_required
def do_borrow(pub_id):
    pub = Publication.query.get_or_404(pub_id)

    # 检查是否已被借阅
    if pub.is_borrowed:
        flash('该出版物已被借出！', 'danger')
        return redirect(url_for('borrow_books'))

    # 创建借阅记录
    borrow_time = datetime.utcnow()
    # 计算到期日期
    loan_days = MAX_BOOK_LOAN_DAYS if pub.type == 'book' else MAX_MAGAZINE_LOAN_DAYS
    due_date = borrow_time + timedelta(days=loan_days)

    record = BorrowRecord(
        user_id=current_user.id,
        publication_id=pub.id,
        borrow_time=borrow_time,
        due_date=due_date,  # 必须设置到期日期
        status='borrowed'
    )

    # 更新出版物状态
    pub.is_borrowed = True

    db.session.add(record)
    db.session.commit()

    flash(f'成功借阅《{pub.title}》！到期时间：{due_date.strftime("%Y-%m-%d")}', 'success')
    return redirect(url_for('my_borrows'))


# 我的借阅记录
@app.route('/reader/my_borrows')
@login_required
def my_borrows():
    # 获取当前用户的所有借阅记录
    borrow_records = BorrowRecord.query.filter_by(user_id=current_user.id).order_by(
        BorrowRecord.borrow_time.desc()
    ).all()

    # 传入当前时间到模板（解决datetime未定义问题）
    current_time = datetime.utcnow()

    return render_template(
        'reader/my_borrows.html',
        borrow_records=borrow_records,
        current_time=current_time  # 新增：传入当前时间
    )

# 归还图书
@app.route('/reader/return/<int:pub_id>')
@login_required
def do_return(pub_id):
    if current_user.role != 'reader':
        flash('权限不足！', 'danger')
        return redirect(url_for('index'))

    pub = Publication.query.get_or_404(pub_id)
    # 检查是否是当前用户借阅的
    if pub.borrower_id != current_user.id:
        flash('你未借阅该出版物！', 'danger')
        return redirect(url_for('my_borrows'))

    success, message = pub.return_book()
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('my_borrows'))


# ---------------- 文档导入路由 ----------------
# 文档上传页面
@app.route('/document/upload', methods=['GET', 'POST'])
@login_required
def upload_document():
    if request.method == 'POST':
        # 检查是否有文件上传
        if 'file' not in request.files:
            flash('未选择文件！', 'danger')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('未选择文件！', 'danger')
            return redirect(request.url)

        # 保存并解析文件
        result, message = save_uploaded_file(file)
        if not result:
            flash(message, 'danger')
            return redirect(request.url)

        # 保存到数据库
        document = Document(
            filename=result['filename'],
            file_path=result['file_path'],
            file_type=result['file_type'],
            content=result['content'],
            translated_content=result['translated_content'],
            uploader_id=current_user.id
        )
        db.session.add(document)
        db.session.commit()

        flash('文档上传并解析成功！', 'success')
        return redirect(url_for('upload_document'))

    # 获取当前用户上传的文档
    documents = Document.query.filter_by(uploader_id=current_user.id).order_by(
        Document.upload_time.desc()
    ).all()

    return render_template('document/upload.html', documents=documents)


# 查看文档内容
@app.route('/document/view/<int:doc_id>')
@login_required
def view_document(doc_id):
    document = Document.query.get_or_404(doc_id)
    # 检查权限
    if document.uploader_id != current_user.id and current_user.role != 'admin':
        flash('无权访问该文档！', 'danger')
        return redirect(url_for('upload_document'))

    return render_template('document/view.html', document=document)




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=6700)