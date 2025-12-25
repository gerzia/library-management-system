import os
import pymysql

# MySQL配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'db': 'book_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Flask配置
SECRET_KEY = os.urandom(24)  # 生产环境请固定密钥
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads/documents')
ALLOWED_EXTENSIONS = {'txt', 'md', 'doc', 'docx', 'pdf'}

# Marker PDF解析配置
MARKER_CONFIG = { "output_format": "markdown", "use_llm": False, "force_ocr": False }

# 借阅配置
MAX_BOOK_LOAN_DAYS = 14
MAX_MAGAZINE_LOAN_DAYS = 7

# 创建上传目录
os.makedirs(UPLOAD_FOLDER, exist_ok=True)