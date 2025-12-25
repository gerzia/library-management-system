from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
import bcrypt
from config import MAX_BOOK_LOAN_DAYS, MAX_MAGAZINE_LOAN_DAYS

# 初始化SQLAlchemy
db = SQLAlchemy()


# ====================== 用户表（管理员/读者） ======================
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # 角色：admin（管理员）/reader（读者），长度调整为20更合理
    role = db.Column(db.String(20), nullable=False, default='reader')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系：用户 -> 借阅记录（一对多）
    borrow_records = db.relationship('BorrowRecord', backref='borrower', lazy=True)
    # 关联关系：用户 -> 上传的文档（一对多）
    uploaded_documents = db.relationship('Document', backref='uploader', lazy=True)

    # 设置密码（bcrypt哈希）
    def set_password(self, password):
        """将明文密码加密后存储"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    # 验证密码
    def check_password(self, password):
        """验证明文密码与哈希密码是否匹配"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except Exception:
            return False


# ====================== 出版物表（图书/杂志） ======================
class Publication(db.Model):
    __tablename__ = 'publications'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, comment='出版物标题')
    type = db.Column(db.String(10), nullable=False, comment='类型：book/magazine')  # book/magazine
    author = db.Column(db.String(100), comment='图书作者')  # 图书专属
    isbn = db.Column(db.String(20), unique=True, comment='图书ISBN')  # 图书专属
    category = db.Column(db.String(50), default='技术', comment='图书分类')  # 图书专属
    issue = db.Column(db.String(20), comment='杂志期号')  # 杂志专属
    publisher = db.Column(db.String(100), comment='杂志出版商')  # 杂志专属
    is_latest = db.Column(db.Boolean, default=True, comment='杂志是否最新')  # 杂志专属
    is_borrowed = db.Column(db.Boolean, default=False, comment='是否已借出')
    borrower_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='借阅人ID')
    due_date = db.Column(db.DateTime, comment='到期归还日期')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 关联关系：出版物 -> 借阅记录（一对多）
    borrow_records = db.relationship('BorrowRecord', backref='publication', lazy=True)

    # 获取最大借阅天数
    def get_max_loan_days(self):
        """根据类型返回最大借阅天数（图书14天，杂志7天）"""
        return MAX_BOOK_LOAN_DAYS if self.type == 'book' else MAX_MAGAZINE_LOAN_DAYS

    # 检查是否逾期（核心修复：移到Publication模型，因为只有它有due_date）
    @property
    def is_overdue(self):
        """判断当前出版物是否逾期未归还"""
        if not self.is_borrowed or not self.due_date:
            return False
        return datetime.utcnow() > self.due_date

    # 借阅操作
    def borrow(self, user):
        """
        借阅出版物
        :param user: 借阅用户对象
        :return: (是否成功, 提示信息)
        """
        # 检查是否已被借出
        if self.is_borrowed:
            due_date_str = self.due_date.strftime('%Y-%m-%d') if self.due_date else '未知时间'
            return False, f"《{self.title}》已被借出，预计{due_date_str}归还"

        try:
            # 更新出版物状态
            self.is_borrowed = True
            self.borrower_id = user.id
            self.due_date = datetime.utcnow() + timedelta(days=self.get_max_loan_days())

            # 创建借阅记录
            record = BorrowRecord(
                publication_id=self.id,
                user_id=user.id,
                borrow_time=datetime.utcnow(),
                status='borrowed'
            )
            db.session.add(record)
            db.session.commit()

            due_date_str = self.due_date.strftime('%Y-%m-%d')
            return True, f"成功借阅《{self.title}》，请于{due_date_str}前归还"
        except Exception as e:
            db.session.rollback()
            return False, f"借阅失败：{str(e)}"

    # 归还操作
    def return_book(self):
        """
        归还出版物
        :return: (是否成功, 提示信息)
        """
        # 检查是否未被借出
        if not self.is_borrowed:
            return False, "该出版物未被借出，无需归还"

        try:
            # 更新借阅记录（标记归还时间和状态）
            record = BorrowRecord.query.filter_by(
                publication_id=self.id,
                user_id=self.borrower_id,
                status='borrowed'
            ).order_by(BorrowRecord.borrow_time.desc()).first()

            if record:
                record.return_time = datetime.utcnow()
                record.status = 'returned'

            # 重置出版物状态
            self.is_borrowed = False
            self.borrower_id = None
            self.due_date = None

            db.session.commit()
            return True, f"成功归还《{self.title}》"
        except Exception as e:
            db.session.rollback()
            return False, f"归还失败：{str(e)}"


# ====================== 借阅记录表 ======================
class BorrowRecord(db.Model):
    __tablename__ = 'borrow_records'
    id = db.Column(db.Integer, primary_key=True)
    publication_id = db.Column(db.Integer, db.ForeignKey('publications.id'), nullable=False, comment='出版物ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='借阅人ID')
    borrow_time = db.Column(db.DateTime, default=datetime.utcnow, comment='借阅时间')
    return_time = db.Column(db.DateTime, comment='归还时间')
    status = db.Column(db.String(10), default='borrowed', comment='状态：borrowed/returned')  # borrowed/returned
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='记录创建时间')

    # 补充：通过借阅记录获取是否逾期（兼容模板逻辑）
    @property
    def is_overdue(self):
        """通过关联的出版物判断是否逾期"""
        return self.publication.is_overdue if self.publication else False


# ====================== 导入文档表 ======================
class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False, comment='文件名')
    file_path = db.Column(db.String(500), nullable=False, comment='文件存储路径')
    file_type = db.Column(db.String(10), nullable=False, comment='文件类型：txt/md/doc/docx/pdf')
    content = db.Column(db.Text, comment='文档原始内容')
    translated_content = db.Column(db.Text, comment='文档翻译后内容')
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='上传人ID')
    upload_time = db.Column(db.DateTime, default=datetime.utcnow, comment='上传时间')