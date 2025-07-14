import os
import re
import zipfile
import tarfile
import tempfile

def extract_archive(archive_path, extract_dir):
    """解压压缩文件到指定目录"""
    if archive_path.endswith('.zip'):
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    elif archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
        with tarfile.open(archive_path, 'r:gz') as tar_ref:
            tar_ref.extractall(extract_dir)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path}")
def is_text_file(file_path):
    """更严格地判断文件是否为文本文件"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read(1024)
            if not content:
                return False
            # 检查是否有非文本字符（高位大于 0x7F 的字符）
            return all(0x07 <= byte <= 0x0D or 0x20 <= byte <= 0xFF for byte in content)
    except Exception:
        return False

def extract_strings(file_path, min_length=4):
    """模拟 strings 命令，提取可读字符串"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        # 匹配连续的可打印字符（ASCII 范围）
        import re
        pattern = re.compile(b'([\\x20-\\x7E]{%d,})' % min_length)
        strings = pattern.findall(content)
        return [s.decode('utf-8', errors='ignore') for s in strings]
    except Exception:
        return []

def scan_file_for_keywords(file_path, keywords, report_file, reported_path=None):
    """扫描文件中的关键字，写入报告"""
    ext = os.path.splitext(file_path)[1].lower()

    # 对 .class 和 .jar 中的文件做特殊处理
    if ext in ('.class', '.jar', '.dex'):
        strings = extract_strings(file_path)
        content = '\n'.join(strings)
        lines = content.splitlines()
    else:
        if not is_text_file(file_path):
            return  # 跳过非文本文件

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return

    for line_num, line in enumerate(lines, start=1):
        for keyword in keywords:
            if re.search(keyword, line, re.IGNORECASE):  # 忽略大小写匹配
                report_file.write(f"{keyword} | {reported_path or file_path} | Line {line_num}: {line.strip()}\n")

def process_directory(directory, keywords, report_file, archive_path=None):
    """递归处理目录下的文件和子目录"""
    for root, _, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)

            if file_name.endswith(('.zip', '.tar.gz', '.tgz')):
                # 解压压缩文件并递归扫描
                with tempfile.TemporaryDirectory() as temp_dir:
                    extract_archive(file_path, temp_dir)
                    # 传入原始压缩文件路径
                    process_directory(temp_dir, keywords, report_file, archive_path=file_path)
            else:
                try:
                    # 构造压缩包内的相对路径
                    if archive_path:
                        internal_path = os.path.relpath(file_path, directory)
                        reported_path = f"{archive_path}\\{internal_path}"
                    else:
                        reported_path = file_path

                    scan_file_for_keywords(file_path, keywords, report_file, reported_path)
                except Exception as e:
                    print(f"Error scanning file {file_path}: {e}")

def main():
    # 配置参数
    path_to_scan = "scanDir"  # 替换为需要扫描的路径
    report_file_path = "scanReport.txt"  # 输出报告文件
    # 关键字
    keywords = ("QMenu", "计算","Class")

    # 清空或创建报告文件
    with open(report_file_path, 'w', encoding='utf-8') as report_file:
        report_file.write("Keyword | File Path | Line Info\n")
        report_file.write("-" * 80 + "\n")
        process_directory(path_to_scan, keywords, report_file)

    print(f"扫描完成，报告已生成至 {report_file_path}")

if __name__ == "__main__":
    main()