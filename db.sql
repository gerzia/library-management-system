-- 创建数据库
CREATE DATABASE IF NOT EXISTS book_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE book_db;

-- 手动创建表（如果ORM创建失败）
DROP TABLE IF EXISTS borrow_records;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS publications;
DROP TABLE IF EXISTS users;

-- 用户表
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(10) NOT NULL DEFAULT 'reader',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 出版物表
CREATE TABLE publications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    type VARCHAR(10) NOT NULL,
    author VARCHAR(100),
    isbn VARCHAR(20) UNIQUE,
    category VARCHAR(50) DEFAULT '技术',
    issue VARCHAR(20),
    publisher VARCHAR(100),
    is_latest BOOLEAN DEFAULT TRUE,
    is_borrowed BOOLEAN DEFAULT FALSE,
    borrower_id INT,
    due_date DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (borrower_id) REFERENCES users(id)
);

-- 借阅记录表
CREATE TABLE borrow_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    publication_id INT NOT NULL,
    user_id INT NOT NULL,
    borrow_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    return_time DATETIME,
    status VARCHAR(10) DEFAULT 'borrowed',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (publication_id) REFERENCES publications(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 文档表
CREATE TABLE documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    content TEXT,
    translated_content TEXT,
    uploader_id INT NOT NULL,
    upload_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploader_id) REFERENCES users(id)
);

-- 测试数据
-- 1. 管理员用户（密码：admin123）
INSERT INTO users (username, password_hash, role) VALUES 
('admin', '$2b$12$EixZaYb4xU58Gpq1R0yWbeb00LU5qUaK65e2r0wX00ePvFjF5G5zu', 'admin'),
('reader1', '$2b$12$EixZaYb4xU58Gpq1R0yWbeb00LU5qUaK65e2r0wX00ePvFjF5G5zu', 'reader'),
('reader2', '$2b$12$EixZaYb4xU58Gpq1R0yWbeb00LU5qUaK65e2r0wX00ePvFjF5G5zu', 'reader');

-- 2. 图书数据
INSERT INTO publications (title, type, author, isbn, category) VALUES
('Python编程：从入门到实践', 'book', '埃里克·马瑟斯', '9787115428028', '编程'),
('Java核心技术 卷1：基础知识', 'book', '凯·霍斯特曼', '9787111641247', '编程'),
('深入理解计算机系统', 'book', '兰德尔·E·布莱恩特', '9787111544937', '计算机基础'),
('算法导论', 'book', '托马斯·科尔曼', '9787111407010', '算法'),
('机器学习', 'book', '周志华', '9787111521242', '人工智能'),
('深度学习', 'book', '伊恩·古德费洛', '9787115461476', '人工智能'),
('MySQL必知必会', 'book', '本·福达', '9787115226108', '数据库'),
('Redis设计与实现', 'book', '黄健宏', '9787115370592', '数据库'),
('Spring实战', 'book', '克雷格·沃斯', '9787115527926', '框架'),
('Django Web开发实战', 'book', '闫令琪', '9787115546081', '框架');

-- 3. 杂志数据
INSERT INTO publications (title, type, issue, publisher, is_latest) VALUES
('程序员 2024年第1期', 'magazine', '2024-01', '程序员杂志社', TRUE),
('计算机应用 2024年第2期', 'magazine', '2024-02', '计算机应用杂志社', TRUE),
('人工智能学报 2024年第3期', 'magazine', '2024-03', '人工智能学报杂志社', FALSE),
('网络安全技术与应用 2024年第1期', 'magazine', '2024-01', '网络安全杂志社', TRUE),
('大数据时代 2024年第2期', 'magazine', '2024-02', '大数据杂志社', TRUE);

-- 4. 借阅记录（测试）
INSERT INTO borrow_records (publication_id, user_id, borrow_time, status) VALUES
(1, 2, '2025-11-01 10:00:00', 'borrowed'),
(2, 3, '2025-11-10 14:00:00', 'returned'),
(3, 2, '2025-10-15 09:00:00', 'returned');

-- 更新出版物借阅状态
UPDATE publications SET is_borrowed = TRUE, borrower_id = 2, due_date = '2025-11-15 10:00:00' WHERE id = 1;
UPDATE publications SET is_borrowed = FALSE, borrower_id = NULL, due_date = NULL WHERE id = 2;
UPDATE publications SET is_borrowed = FALSE, borrower_id = NULL, due_date = NULL WHERE id = 3;
