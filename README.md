# 图书馆管理系统（Library Management System）
基于 Flask + MySQL 开发的轻量级图书馆管理系统，采用面向对象设计思想，支持管理员/读者双角色，实现出版物管理、借阅归还、文档导入翻译等核心功能,用作软件工程课程设计或者专业毕业设计。

## 项目介绍
本系统是软件工程课程综合实践项目，基于**面向对象方法学**完成分析、设计与实现，核心目标是解决中小型图书馆的出版物管理、借阅流程自动化问题，具备以下特性：
- 多角色权限控制（管理员/读者）
- 出版物（图书/杂志）全生命周期管理
- 借阅归还流程自动化 + 逾期提醒
- 多格式文档（TXT/MD/DOC/DOCX/PDF）导入、解析、英文自动翻译
- 美观的 Bootstrap 5 前端界面，适配移动端
- 严格的密码哈希加密，保障数据安全

## 技术栈
| 分类       | 技术/工具                          |
|------------|------------------------------------|
| 后端       | Python 3.10+、Flask 2.3.3、Flask-SQLAlchemy、Flask-Login |
| 数据库     | MySQL 8.0（Ubuntu 版）|
| 前端       | HTML5、CSS3、Bootstrap 5、JavaScript |
| 文档处理   | python-docx、PyPDF2、Marker（PDF解析） |
| 安全       | bcrypt（密码哈希）|
| 翻译       | translators（有道翻译接口）|

## 环境要求（Ubuntu 系统）
1. 操作系统：Ubuntu 20.04/22.04（推荐 LTS 版本）
2. Python：3.10 及以上（Ubuntu 22.04 默认自带 3.10，可通过 `python3 --version` 验证）
3. MySQL：8.0 及以上
4. 依赖库：见 `requirements.txt`
## 演示效果
### 读者仪表盘：
<img width="2489" height="1242" alt="a0d84f8b0f477bc28913051bb4feb499" src="https://github.com/user-attachments/assets/ed0129f4-8fbb-48d1-b247-565c50e005fe" />

### 借阅页面（支持模糊搜索）:
<img width="2489" height="1242" alt="image" src="https://github.com/user-attachments/assets/3b1a8bd5-4308-4194-a4be-a9753654efc6" />

### 我的借阅记录:
<img width="2489" height="1242" alt="image" src="https://github.com/user-attachments/assets/b487ede4-1328-4a39-906c-c0297624f24b" />

### 文档解析:
<img width="2489" height="1242" alt="image" src="https://github.com/user-attachments/assets/1e867dd4-7102-492e-843a-4c8072e8b397" />


## 部署步骤（Ubuntu 系统）
### 1. 克隆项目（本地/服务器）
```bash
# 若未安装 Git，先执行：
sudo apt update && sudo apt install git -y

# 克隆 GitHub 仓库（替换为你的仓库地址）
https://github.com/gerzia/library-management-system.git
cd library-management-system
pip install -r requirements.txt
# 运行网站
python app.py

