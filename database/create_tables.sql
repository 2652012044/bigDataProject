-- ========================================
-- 小说大数据平台 - 数据库建表脚本
-- 基于番茄小说爬虫数据格式修正
-- ========================================

CREATE DATABASE IF NOT EXISTS novel_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE novel_db;

-- =========================
-- 分类表 category
-- =========================
-- category_id 使用番茄小说原始ID，不自增
CREATE TABLE IF NOT EXISTS category (
    category_id BIGINT PRIMARY KEY COMMENT '番茄原始分类ID',
    name VARCHAR(64) NOT NULL COMMENT '分类名称，如：玄幻、都市',
    tab_name VARCHAR(20) COMMENT '频道名：男生/女生',
    category_tab TINYINT COMMENT '频道编号：1=男生 2=女生',
    cell_name VARCHAR(30) COMMENT '所属区块：热门标签等',
    show_type TINYINT COMMENT '展示类型',
    style TINYINT COMMENT '样式',
    category_landpage_url VARCHAR(512) COMMENT '分类落地页URL',
    pic_url VARCHAR(512) COMMENT '分类图标URL'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分类表';


-- =========================
-- 作者表 author
-- =========================
-- author_id 使用番茄原始 user_id，不自增
CREATE TABLE IF NOT EXISTS author (
    author_id BIGINT PRIMARY KEY COMMENT '番茄原始用户ID',
    author_name VARCHAR(128) COMMENT '作者名',
    author_type TINYINT COMMENT '用户类型',
    gender TINYINT COMMENT '性别：0未知 1男 2女',
    description VARCHAR(1024) COMMENT '作者简介',
    user_avatar VARCHAR(512) COMMENT '头像URL',

    read_book_time BIGINT COMMENT '阅读时长(秒)',
    read_book_num INT COMMENT '阅读书籍数',
    recv_digg_num INT COMMENT '获赞数',

    fans_num INT COMMENT '粉丝数',
    follow_user_num INT COMMENT '关注数',
    author_book_num INT COMMENT '作品数',

    is_author TINYINT DEFAULT 0 COMMENT '是否作者',
    is_vip TINYINT DEFAULT 0 COMMENT '是否VIP',
    is_official_cert TINYINT DEFAULT 0 COMMENT '是否官方认证',
    has_medal TINYINT DEFAULT 0 COMMENT '是否有勋章',
    is_cancelled TINYINT DEFAULT 0 COMMENT '是否注销'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='作者表';


-- =========================
-- 书籍表 book
-- =========================
-- book_id 使用番茄原始ID，不自增
CREATE TABLE IF NOT EXISTS book (
    book_id BIGINT PRIMARY KEY COMMENT '番茄原始书籍ID',
    book_name VARCHAR(255) NOT NULL COMMENT '书名',
    author VARCHAR(128) COMMENT '作者名',
    author_id BIGINT COMMENT '关联 author.author_id',
    score DECIMAL(3,1) DEFAULT 0 COMMENT '评分',
    word_number BIGINT DEFAULT 0 COMMENT '字数',
    creation_status TINYINT COMMENT '创作状态：0连载中 1完结',
    update_status TINYINT COMMENT '更新状态',
    read_count BIGINT DEFAULT 0 COMMENT '阅读人数',
    read_count_text VARCHAR(32) COMMENT '阅读人数文本，如1.3万人在读',
    chapter_number INT COMMENT '章节数',
    serial_count INT COMMENT '连载章数',
    category VARCHAR(64) COMMENT '分类名称',
    tags VARCHAR(512) COMMENT '标签，逗号分隔',
    abstract TEXT COMMENT '书籍简介',
    thumb_url VARCHAR(512) COMMENT '封面图URL',
    book_short_name VARCHAR(128) COMMENT '书籍简称',
    genre TINYINT COMMENT '类型：0男频 1女频',
    platform TINYINT COMMENT '平台',
    comment_total INT DEFAULT 0 COMMENT '总评论数',

    INDEX idx_author_id (author_id),
    INDEX idx_category (category),
    INDEX idx_score (score),
    INDEX idx_read_count (read_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='书籍表';


-- =========================
-- 标签表 tag + 书籍标签关联表 book_tag
-- =========================
CREATE TABLE IF NOT EXISTS tag (
    tag_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '标签ID',
    tag_name VARCHAR(64) NOT NULL UNIQUE COMMENT '标签名称',

    INDEX idx_tag_name (tag_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='标签表';

CREATE TABLE IF NOT EXISTS book_tag (
    book_id BIGINT NOT NULL COMMENT '关联 book.book_id',
    tag_id INT NOT NULL COMMENT '关联 tag.tag_id',
    PRIMARY KEY (book_id, tag_id),

    INDEX idx_tag_id (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='书籍-标签关联表';


-- =========================
-- 评论表 comment
-- =========================
-- comment_id 使用番茄原始ID，不自增
CREATE TABLE IF NOT EXISTS comment (
    comment_id BIGINT PRIMARY KEY COMMENT '番茄原始评论ID',
    book_id BIGINT NOT NULL COMMENT '关联 book.book_id',
    content TEXT COMMENT '评论内容',
    content_type TINYINT DEFAULT 0 COMMENT '内容类型',
    create_timestamp BIGINT COMMENT '评论时间戳(秒)',
    user_id BIGINT COMMENT '评论用户ID',
    user_name VARCHAR(128) COMMENT '评论用户名',
    digg_count INT DEFAULT 0 COMMENT '点赞数',
    reply_count INT DEFAULT 0 COMMENT '回复数',
    show_pv INT DEFAULT 0 COMMENT '浏览量',
    status TINYINT DEFAULT 1 COMMENT '状态',

    INDEX idx_book_id (book_id),
    INDEX idx_create_timestamp (create_timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评论表';


-- =========================
-- 网站用户表 web_user（平台登录用）
-- =========================
CREATE TABLE IF NOT EXISTS web_user (
    user_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(64) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码(加密存储)',
    email VARCHAR(128) UNIQUE COMMENT '邮箱',
    phone VARCHAR(20) UNIQUE COMMENT '手机号',
    avatar VARCHAR(512) COMMENT '头像URL',
    role TINYINT DEFAULT 0 COMMENT '0普通用户 1管理员',
    status TINYINT DEFAULT 1 COMMENT '1正常 0禁用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='网站用户表';


-- =========================
-- 用户收藏表 user_favorite
-- =========================
CREATE TABLE IF NOT EXISTS user_favorite (
    user_id BIGINT NOT NULL COMMENT '关联 web_user.user_id',
    book_id BIGINT NOT NULL COMMENT '关联 book.book_id',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
    PRIMARY KEY (user_id, book_id),

    INDEX idx_user_id (user_id),
    INDEX idx_book_id (book_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户收藏表';
