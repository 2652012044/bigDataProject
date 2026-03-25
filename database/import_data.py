# -*- coding: utf-8 -*-
"""
小说大数据平台 - 自动化数据导入脚本
功能：将爬虫获取的 JSON 数据导入 MySQL 数据库
特性：
  - 支持去重（INSERT ... ON DUPLICATE KEY UPDATE）
  - 可重复运行，不会导入重复数据
  - 支持处理整个文件夹
  - 自动跳过无效数据（book_id=0 等）
用法：
  python import_data.py
"""

import json
import os
import sys
import configparser
import pymysql
import logging
from datetime import datetime

# ============ 数据库配置（从 db_config.ini 读取，避免密码入 Git） ============
_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db_config.ini')
if not os.path.exists(_config_path):
    print(f"[错误] 找不到配置文件: {_config_path}")
    print("请复制 db_config.example.ini 为 db_config.ini，填写你的 MySQL 密码")
    sys.exit(1)

_cfg = configparser.ConfigParser()
_cfg.read(_config_path, encoding='utf-8')

DB_CONFIG = {
    'host': _cfg.get('mysql', 'host', fallback='127.0.0.1'),
    'port': _cfg.getint('mysql', 'port', fallback=3306),
    'user': _cfg.get('mysql', 'user', fallback='root'),
    'password': _cfg.get('mysql', 'password'),
    'database': _cfg.get('mysql', 'database', fallback='novel_db'),
    'charset': 'utf8mb4',
}

# ============ 数据目录 ============
DATA_DIR = r'D:\bigDataProject\fqDataAPI_mitproxy\data'

# ============ 工具函数 ============

def get_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)


def safe_int(val, default=0):
    """安全转整数"""
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def safe_float(val, default=0.0):
    """安全转浮点数"""
    if val is None:
        return default
    try:
        f = float(val)
        return f if f > 0 else default
    except (ValueError, TypeError):
        return default


def read_json(filepath):
    """读取 JSON 文件，自动处理编码"""
    for encoding in ['utf-8', 'utf-8-sig', 'gbk']:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return json.load(f)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    print(f"  [警告] 无法读取文件: {filepath}")
    return None


# ============ 导入函数 ============

def import_categories(conn):
    """导入分类数据 CategoryList.json"""
    filepath = os.path.join(DATA_DIR, 'CategoryList.json')
    if not os.path.exists(filepath):
        print("[跳过] CategoryList.json 不存在")
        return

    print("\n===== 导入分类数据 =====")
    data = read_json(filepath)
    if not data:
        return

    cursor = conn.cursor()
    count = 0
    for item in data:
        cid = safe_int(item.get('category_id'))
        if cid <= 0:
            continue
        sql = """
            INSERT INTO category (category_id, name, tab_name, category_tab, cell_name, show_type, style, category_landpage_url, pic_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                tab_name = VALUES(tab_name),
                category_tab = VALUES(category_tab),
                cell_name = VALUES(cell_name),
                pic_url = VALUES(pic_url)
        """
        cursor.execute(sql, (
            cid,
            item.get('name', ''),
            item.get('tab_name', ''),
            safe_int(item.get('category_tab')),
            item.get('cell_name', ''),
            safe_int(item.get('show_type')),
            safe_int(item.get('style')),
            item.get('category_landpage_url', ''),
            item.get('pic_url', ''),
        ))
        count += 1

    conn.commit()
    print(f"  处理了 {count} 条分类记录")


def import_booklist(conn):
    """导入书籍列表 BookList.json"""
    filepath = os.path.join(DATA_DIR, 'BookList.json')
    if not os.path.exists(filepath):
        print("[跳过] BookList.json 不存在")
        return

    print("\n===== 导入书籍列表 =====")
    data = read_json(filepath)
    if not data or not isinstance(data, dict):
        return

    cursor = conn.cursor()
    count = 0
    for category_name, books in data.items():
        if not isinstance(books, list):
            continue
        for book in books:
            bid = safe_int(book.get('book_id'))
            if bid <= 0:
                continue

            tags = book.get('tags', '')
            if isinstance(tags, list):
                tags = ','.join(str(t) for t in tags if t)

            sql = """
                INSERT INTO book (book_id, book_name, author, score, word_number, category, tags,
                                  creation_status, update_status, read_count, chapter_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    book_name = VALUES(book_name),
                    author = COALESCE(NULLIF(VALUES(author), ''), author),
                    score = GREATEST(score, VALUES(score)),
                    word_number = GREATEST(word_number, VALUES(word_number)),
                    category = COALESCE(NULLIF(VALUES(category), ''), category),
                    tags = COALESCE(NULLIF(VALUES(tags), ''), tags),
                    read_count = GREATEST(read_count, VALUES(read_count))
            """
            cursor.execute(sql, (
                bid,
                book.get('book_name', ''),
                book.get('author', '') or '',
                safe_float(book.get('score')),
                safe_int(book.get('word_number')),
                book.get('category', '') or category_name,
                tags,
                safe_int(book.get('creation_status')),
                safe_int(book.get('update_status')),
                safe_int(book.get('read_count')),
                safe_int(book.get('chapter_number')) if book.get('chapter_number') else None,
            ))
            count += 1

            # 同时处理标签
            _import_tags_for_book(cursor, bid, tags)

    conn.commit()
    print(f"  处理了 {count} 条书籍记录")


def import_bookinfo(conn):
    """导入书籍详情 bookInfo/*.json"""
    book_dir = os.path.join(DATA_DIR, 'bookInfo')
    if not os.path.isdir(book_dir):
        print("[跳过] bookInfo 目录不存在")
        return

    print("\n===== 导入书籍详情 =====")
    cursor = conn.cursor()
    files = [f for f in os.listdir(book_dir) if f.endswith('.json')]
    count_book = 0
    count_comment = 0

    for fname in files:
        filepath = os.path.join(book_dir, fname)
        data = read_json(filepath)
        if not data:
            continue

        bid = safe_int(data.get('book_id'))
        if bid <= 0:
            continue

        tags = data.get('tags', '')
        if isinstance(tags, list):
            tags = ','.join(str(t) for t in tags if t)

        sql = """
            INSERT INTO book (book_id, book_name, author, score, word_number, tags,
                              creation_status, serial_count, abstract, read_count_text, comment_total)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                book_name = VALUES(book_name),
                author = COALESCE(NULLIF(VALUES(author), ''), author),
                score = GREATEST(score, VALUES(score)),
                word_number = GREATEST(word_number, VALUES(word_number)),
                tags = COALESCE(NULLIF(VALUES(tags), ''), tags),
                serial_count = COALESCE(VALUES(serial_count), serial_count),
                abstract = COALESCE(NULLIF(VALUES(abstract), ''), abstract),
                read_count_text = COALESCE(NULLIF(VALUES(read_count_text), ''), read_count_text),
                comment_total = GREATEST(COALESCE(comment_total, 0), VALUES(comment_total))
        """
        cursor.execute(sql, (
            bid,
            data.get('book_name', ''),
            data.get('author', '') or '',
            safe_float(data.get('score')),
            safe_int(data.get('word_number')),
            tags,
            safe_int(data.get('creation_status')),
            safe_int(data.get('serial_count')),
            data.get('abstract', ''),
            data.get('read_count_text', ''),
            safe_int(data.get('comment_total')),
        ))
        count_book += 1

        # 处理标签
        _import_tags_for_book(cursor, bid, tags)

        # 导入 bookInfo 内嵌的评论
        comments = data.get('comments', [])
        for c in comments:
            cid = safe_int(c.get('comment_id'))
            if cid <= 0:
                continue
            csql = """
                INSERT INTO comment (comment_id, book_id, content, create_timestamp, user_id, user_name, digg_count, reply_count, show_pv)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    digg_count = GREATEST(digg_count, VALUES(digg_count)),
                    reply_count = GREATEST(reply_count, VALUES(reply_count)),
                    show_pv = GREATEST(show_pv, VALUES(show_pv))
            """
            cursor.execute(csql, (
                cid, bid,
                c.get('text', ''),
                safe_int(c.get('create_timestamp')),
                safe_int(c.get('user_id')),
                c.get('user_name', ''),
                safe_int(c.get('digg_count')),
                safe_int(c.get('reply_count')),
                safe_int(c.get('show_pv')),
            ))
            count_comment += 1

        print(f"  书籍: {data.get('book_name', fname)} - {len(comments)} 条评论")

    conn.commit()
    print(f"  共处理 {count_book} 本书详情，{count_comment} 条评论")


def import_userinfo(conn):
    """导入作者信息 userInfo/*.json"""
    user_dir = os.path.join(DATA_DIR, 'userInfo')
    if not os.path.isdir(user_dir):
        print("[跳过] userInfo 目录不存在")
        return

    print("\n===== 导入作者信息 =====")
    cursor = conn.cursor()
    files = [f for f in os.listdir(user_dir) if f.endswith('.json')]
    count = 0

    for fname in files:
        filepath = os.path.join(user_dir, fname)
        data = read_json(filepath)
        if not data:
            continue

        # 数据可能有外层 {code, data} 包装
        if 'data' in data and isinstance(data['data'], dict):
            info = data['data']
        else:
            info = data

        uid = safe_int(info.get('user_id'))
        if uid <= 0:
            continue

        sql = """
            INSERT INTO author (author_id, author_name, author_type, gender, description, user_avatar,
                                read_book_time, read_book_num, recv_digg_num, is_author)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                author_name = VALUES(author_name),
                description = COALESCE(NULLIF(VALUES(description), ''), description),
                user_avatar = COALESCE(NULLIF(VALUES(user_avatar), ''), user_avatar),
                read_book_time = GREATEST(COALESCE(read_book_time, 0), VALUES(read_book_time)),
                read_book_num = GREATEST(COALESCE(read_book_num, 0), VALUES(read_book_num)),
                recv_digg_num = GREATEST(COALESCE(recv_digg_num, 0), VALUES(recv_digg_num))
        """
        cursor.execute(sql, (
            uid,
            info.get('user_name', ''),
            safe_int(info.get('user_type')),
            safe_int(info.get('gender')),
            info.get('description', ''),
            info.get('user_avatar', ''),
            safe_int(info.get('read_book_time')),
            safe_int(info.get('read_book_num')),
            safe_int(info.get('recv_digg_num')),
            1 if info.get('is_author') else 0,
        ))
        count += 1

        # 同时从作者的作品列表补充书籍信息
        author_books = info.get('author_book_info', [])
        for ab in author_books:
            abid = safe_int(ab.get('book_id'))
            if abid <= 0:
                continue

            tags = ab.get('tags', '')
            if isinstance(tags, list):
                tags = ','.join(str(t) for t in tags if t)

            bsql = """
                INSERT INTO book (book_id, book_name, author, author_id, score, word_number,
                                  category, tags, creation_status, read_count, read_count_text,
                                  thumb_url, book_short_name, genre, platform)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    author_id = COALESCE(VALUES(author_id), author_id),
                    score = GREATEST(score, VALUES(score)),
                    word_number = GREATEST(word_number, VALUES(word_number)),
                    category = COALESCE(NULLIF(VALUES(category), ''), category),
                    tags = COALESCE(NULLIF(VALUES(tags), ''), tags),
                    read_count = GREATEST(read_count, VALUES(read_count)),
                    thumb_url = COALESCE(NULLIF(VALUES(thumb_url), ''), thumb_url),
                    book_short_name = COALESCE(NULLIF(VALUES(book_short_name), ''), book_short_name)
            """
            cursor.execute(bsql, (
                abid,
                ab.get('book_name', ''),
                ab.get('author', ''),
                uid,
                safe_float(ab.get('score')),
                safe_int(ab.get('word_number')),
                ab.get('category', ''),
                tags,
                safe_int(ab.get('creation_status')),
                safe_int(ab.get('read_count')),
                ab.get('read_cnt_text', ''),
                ab.get('thumb_url', ''),
                ab.get('book_short_name', ''),
                safe_int(ab.get('genre')),
                safe_int(ab.get('platform')),
            ))

        print(f"  作者: {info.get('user_name', fname)} - {len(author_books)} 部作品")

    conn.commit()
    print(f"  共处理 {count} 位作者")


def import_comments(conn):
    """导入评论详情 comtJson/*/body_*.json"""
    comt_dir = os.path.join(DATA_DIR, 'comtJson')
    if not os.path.isdir(comt_dir):
        print("[跳过] comtJson 目录不存在")
        return

    print("\n===== 导入评论数据 =====")
    cursor = conn.cursor()
    total_count = 0

    for book_folder in os.listdir(comt_dir):
        folder_path = os.path.join(comt_dir, book_folder)
        if not os.path.isdir(folder_path):
            continue

        body_files = [f for f in os.listdir(folder_path) if f.startswith('body_') and f.endswith('.json')]
        folder_count = 0

        for fname in body_files:
            filepath = os.path.join(folder_path, fname)
            data = read_json(filepath)
            if not data:
                continue

            # 提取评论列表
            data_section = data.get('data', {})
            data_list = data_section.get('data_list', [])

            for item in data_list:
                comment = item.get('comment', {})
                if not comment:
                    continue

                cid = safe_int(comment.get('comment_id'))
                if cid <= 0:
                    continue

                common = comment.get('common', {})
                content = common.get('content', {})
                user_info = common.get('user_info', {}).get('base_info', {})
                stat = comment.get('stat', {})
                expand = comment.get('expand', {})

                book_id = safe_int(expand.get('book_id') or common.get('group_id'))
                if book_id <= 0:
                    continue

                sql = """
                    INSERT INTO comment (comment_id, book_id, content, content_type, create_timestamp,
                                         user_id, user_name, digg_count, reply_count, show_pv, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        digg_count = GREATEST(digg_count, VALUES(digg_count)),
                        reply_count = GREATEST(reply_count, VALUES(reply_count)),
                        show_pv = GREATEST(show_pv, VALUES(show_pv))
                """
                cursor.execute(sql, (
                    cid,
                    book_id,
                    content.get('text', ''),
                    safe_int(common.get('content_type')),
                    safe_int(common.get('create_timestamp')),
                    safe_int(user_info.get('user_id')),
                    user_info.get('user_name', ''),
                    safe_int(stat.get('digg_count')),
                    safe_int(stat.get('reply_count')),
                    safe_int(stat.get('show_pv')),
                    safe_int(common.get('status', 1)),
                ))
                folder_count += 1

        if folder_count > 0:
            print(f"  {book_folder}: {folder_count} 条评论")
        total_count += folder_count

    conn.commit()
    print(f"  共处理 {total_count} 条评论")


def import_booklist_tabs(conn):
    """导入分类书单 bookListTab_* 文件夹/文件"""
    print("\n===== 导入分类书单 =====")
    cursor = conn.cursor()
    count = 0

    for item_name in os.listdir(DATA_DIR):
        if not item_name.startswith('bookListTab_'):
            continue

        item_path = os.path.join(DATA_DIR, item_name)
        category_name = item_name.replace('bookListTab_', '')

        # 可能是文件夹或直接JSON文件
        json_files = []
        if os.path.isdir(item_path):
            json_files = [os.path.join(item_path, f) for f in os.listdir(item_path) if f.endswith('.json')]
        elif os.path.isfile(item_path) and item_name.endswith('.json'):
            json_files = [item_path]

        # bookListTab_ 是文件夹名，尝试读取里面的内容
        if os.path.isdir(item_path):
            for fname in os.listdir(item_path):
                fpath = os.path.join(item_path, fname)
                if not fname.endswith('.json'):
                    continue
                data = read_json(fpath)
                if not data:
                    continue

                books = []
                if isinstance(data, list):
                    books = data
                elif isinstance(data, dict):
                    # 可能有 data.data 嵌套
                    if 'data' in data:
                        inner = data['data']
                        if isinstance(inner, list):
                            books = inner
                        elif isinstance(inner, dict):
                            books = inner.get('book_list', inner.get('list', []))

                for book in books:
                    if not isinstance(book, dict):
                        continue
                    bid = safe_int(book.get('book_id'))
                    if bid <= 0:
                        continue

                    tags = book.get('tags', '')
                    if isinstance(tags, list):
                        tags = ','.join(str(t) for t in tags if t)

                    sql = """
                        INSERT INTO book (book_id, book_name, author, score, word_number, category, tags,
                                          creation_status, read_count, thumb_url)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            score = GREATEST(score, VALUES(score)),
                            word_number = GREATEST(word_number, VALUES(word_number)),
                            category = COALESCE(NULLIF(VALUES(category), ''), category),
                            tags = COALESCE(NULLIF(VALUES(tags), ''), tags),
                            read_count = GREATEST(read_count, VALUES(read_count)),
                            thumb_url = COALESCE(NULLIF(VALUES(thumb_url), ''), thumb_url)
                    """
                    cursor.execute(sql, (
                        bid,
                        book.get('book_name', ''),
                        book.get('author', '') or '',
                        safe_float(book.get('score')),
                        safe_int(book.get('word_number')),
                        book.get('category', '') or category_name,
                        tags,
                        safe_int(book.get('creation_status')),
                        safe_int(book.get('read_count')),
                        book.get('thumb_url', ''),
                    ))
                    count += 1

    conn.commit()
    print(f"  处理了 {count} 条分类书单记录")


def _import_tags_for_book(cursor, book_id, tags_str):
    """将标签字符串拆分导入 tag + book_tag 表"""
    if not tags_str or not isinstance(tags_str, str):
        return
    tag_names = [t.strip() for t in tags_str.split(',') if t.strip()]
    for tag_name in tag_names:
        # 插入标签（去重）
        cursor.execute(
            "INSERT INTO tag (tag_name) VALUES (%s) ON DUPLICATE KEY UPDATE tag_name = tag_name",
            (tag_name,)
        )
        # 获取 tag_id
        cursor.execute("SELECT tag_id FROM tag WHERE tag_name = %s", (tag_name,))
        row = cursor.fetchone()
        if row:
            tag_id = row[0]
            cursor.execute(
                "INSERT INTO book_tag (book_id, tag_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE tag_id = tag_id",
                (book_id, tag_id)
            )


# ============ 日志配置 ============
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cleaning_logs.json')


def _load_logs():
    """加载已有日志"""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return []


def _save_logs(logs):
    """保存日志"""
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


# ============ 主流程 ============

def main():
    print("=" * 50)
    print("小说大数据平台 - 数据导入工具")
    print(f"数据目录: {DATA_DIR}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 初始化本次运行的日志记录
    run_log = {
        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': '',
        'status': 'running',
        'data_dir': DATA_DIR,
        'steps': [],
        'summary': {},
        'errors': []
    }

    # 检查数据目录
    if not os.path.isdir(DATA_DIR):
        print(f"[错误] 数据目录不存在: {DATA_DIR}")
        run_log['status'] = 'failed'
        run_log['errors'].append(f"数据目录不存在: {DATA_DIR}")
        run_log['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logs = _load_logs()
        logs.append(run_log)
        _save_logs(logs)
        sys.exit(1)

    # 连接数据库
    try:
        conn = get_connection()
        print("[成功] 数据库连接成功")
        run_log['steps'].append({'step': '数据库连接', 'status': '成功', 'detail': f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"})
    except Exception as e:
        print(f"[错误] 数据库连接失败: {e}")
        run_log['status'] = 'failed'
        run_log['errors'].append(f"数据库连接失败: {str(e)}")
        run_log['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logs = _load_logs()
        logs.append(run_log)
        _save_logs(logs)
        sys.exit(1)

    try:
        # 按顺序导入各类数据，记录每步结果
        steps_funcs = [
            ('分类数据', import_categories),
            ('书籍列表', import_booklist),
            ('书籍详情', import_bookinfo),
            ('作者信息', import_userinfo),
            ('评论数据', import_comments),
            ('分类书单', import_booklist_tabs),
        ]

        for step_name, func in steps_funcs:
            step_start = datetime.now()
            try:
                func(conn)
                step_info = {
                    'step': step_name,
                    'status': '成功',
                    'duration_ms': int((datetime.now() - step_start).total_seconds() * 1000)
                }
            except Exception as e:
                step_info = {
                    'step': step_name,
                    'status': '失败',
                    'error': str(e),
                    'duration_ms': int((datetime.now() - step_start).total_seconds() * 1000)
                }
                run_log['errors'].append(f"{step_name}: {str(e)}")
            run_log['steps'].append(step_info)

        print("\n" + "=" * 50)
        print("导入完成！")

        # 打印统计并记录
        cursor = conn.cursor()
        tables = ['category', 'author', 'book', 'tag', 'book_tag', 'comment']
        table_stats = {}
        for t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = cursor.fetchone()[0]
            print(f"  {t}: {cnt} 条记录")
            table_stats[t] = cnt

        run_log['summary'] = table_stats
        run_log['status'] = 'success' if not run_log['errors'] else 'partial'
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)

    except Exception as e:
        print(f"\n[错误] 导入过程出错: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        run_log['status'] = 'failed'
        run_log['errors'].append(str(e))
    finally:
        conn.close()
        run_log['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 保存日志
        logs = _load_logs()
        logs.append(run_log)
        _save_logs(logs)
        print(f"\n日志已保存到: {LOG_FILE}")


if __name__ == '__main__':
    main()
