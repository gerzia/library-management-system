import os
import shutil
import hashlib
from docx import Document as DocxDocument
from PyPDF2 import PdfReader
import translators as ts
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
from marker.output import text_from_rendered
from config import UPLOAD_FOLDER, MARKER_CONFIG

# 初始化Marker PDF解析器（保留原代码）
config_parser = ConfigParser(MARKER_CONFIG)
pdf_converter = PdfConverter(
    config=config_parser.generate_config_dict(),
    artifact_dict=create_model_dict(),
    processor_list=config_parser.get_processors(),
    renderer=config_parser.get_renderer(),
    llm_service=config_parser.get_llm_service()
)


# 检查允许的文件类型（保留原代码）
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'txt', 'md', 'doc', 'docx', 'pdf'}


# ========== 修复：重构哈希计算函数 ==========
def generate_file_hash(file_obj, is_stream=True):
    """
    计算文件哈希值
    :param file_obj: 文件流对象 或 文件路径字符串
    :param is_stream: 是否为文件流（True）或文件路径（False）
    :return: 哈希值字符串
    """
    hash_md5 = hashlib.md5()
    try:
        if is_stream:
            # 处理文件流：先重置指针，再分块读取
            file_obj.seek(0)
            for chunk in iter(lambda: file_obj.read(4096), b""):
                hash_md5.update(chunk)
            # 重置指针，供后续使用
            file_obj.seek(0)
        else:
            # 处理文件路径
            with open(file_obj, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"计算文件哈希失败：{e}")
        # 生成随机哈希避免冲突
        return hashlib.md5(str(os.urandom(16)).encode()).hexdigest()


# 解析文档内容（保留原代码，增加异常捕获）
def parse_document(file_path, file_type):
    content = ""
    try:
        if file_type in ['txt', 'md']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        elif file_type in ['doc', 'docx']:
            doc = DocxDocument(file_path)
            for para in doc.paragraphs:
                content += para.text + '\n'
        elif file_type == 'pdf':
            # 使用Marker解析PDF为markdown
            rendered = pdf_converter(file_path)
            content, _, _ = text_from_rendered(rendered)
    except Exception as e:
        print(f"解析文档失败: {e}")
        content = f"解析失败: {str(e)}"
    return content.strip()


# 翻译文本（英文转中文，保留原代码）
def translate_text(text):
    try:
        # 判断是否为英文（简单判断：包含较多英文字母）
        english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
        total_chars = sum(1 for c in text if c.isalpha())
        if total_chars > 0 and english_chars / total_chars > 0.8:
            translated = ts.translate_text(text, translator='youdao', to_language='zh')
            return translated
        return text
    except Exception as e:
        print(f"翻译失败: {e}")
        return text


# ========== 修复：重构文件保存函数 ==========
def save_uploaded_file(file):
    """
    保存上传的文件并解析内容
    :param file: Flask上传的File对象
    :return: (结果字典/None, 提示信息)
    """
    try:
        if not allowed_file(file.filename):
            return None, "不支持的文件类型（仅支持txt/md/doc/docx/pdf）"

        # 1. 生成临时文件路径（先保存文件）
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        temp_filename = f"temp_{hash(file.filename)}_{os.urandom(4).hex()}.{file_ext}"
        temp_file_path = os.path.join(UPLOAD_FOLDER, temp_filename)

        # 2. 保存临时文件（关键：先保存再计算哈希）
        file.stream.seek(0)  # 重置文件流指针
        with open(temp_file_path, 'wb') as f:
            shutil.copyfileobj(file.stream, f)

        # 3. 计算文件哈希（传文件路径，而非文件流）
        file_hash = generate_file_hash(temp_file_path, is_stream=False)

        # 4. 生成最终文件名（避免重复）
        final_filename = f"{file_hash}.{file_ext}"
        final_file_path = os.path.join(UPLOAD_FOLDER, final_filename)

        # 5. 移动/重命名临时文件（避免重复保存）
        if not os.path.exists(final_file_path):
            os.rename(temp_file_path, final_file_path)
        else:
            # 如果文件已存在，删除临时文件
            os.remove(temp_file_path)

        # 6. 解析文件内容
        content = parse_document(final_file_path, file_ext)
        # 7. 翻译内容
        translated_content = translate_text(content)

        return {
            'filename': final_filename,
            'file_path': final_file_path,
            'file_type': file_ext,
            'content': content,
            'translated_content': translated_content
        }, "成功"

    except Exception as e:
        print(f"保存上传文件失败：{e}")
        # 清理临时文件
        try:
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except:
            pass
        return None, f"文件处理失败：{str(e)}"