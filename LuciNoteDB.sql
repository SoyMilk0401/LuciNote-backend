CREATE DATABASE LuciNoteDB
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_cs;

USE LuciNoteDB;

ALTER DATABASE LuciNoteDB
  COLLATE = utf8mb4_bin;

-- 사용자 테이블
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP NULL,
    is_admin BOOLEAN DEFAULT FALSE
);

-- 소셜 로그인 정보 테이블
CREATE TABLE user_providers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    provider VARCHAR(20) NOT NULL, -- ENUM 대신 VARCHAR
    provider_user_id VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL,
    display_name VARCHAR(100),
    profile_image_url VARCHAR(255),
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    UNIQUE (provider, provider_user_id)
);

-- 자료 테이블
CREATE TABLE materials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255),
    material_type ENUM('pdf', 'txt', 'image', 'url') NOT NULL,
    source_file_path VARCHAR(500),
    original_url TEXT,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
    -- CHECK 제약은 MySQL 8 이상에서 아래처럼 사용 가능
    -- CHECK (
    --     (material_type IN ('pdf', 'txt', 'image') AND source_file_path IS NOT NULL AND original_url IS NULL) OR
    --     (material_type = 'url' AND original_url IS NOT NULL AND source_file_path IS NULL)
    -- )
);

-- 요약 테이블
CREATE TABLE summaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    material_id INT NOT NULL,
    summary_title VARCHAR(255),
    summary_text MEDIUMTEXT,
    result_file_path VARCHAR(500),
    format ENUM('txt', 'pdf', 'docx') DEFAULT 'pdf',
    language VARCHAR(10) DEFAULT 'ko',
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES materials(id)
        ON DELETE CASCADE
);

-- 북마크 테이블
CREATE TABLE bookmarks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

-- 북마크 항목 (자료/요약 다형적 연결)
CREATE TABLE bookmark_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bookmark_id INT NOT NULL,
    item_type ENUM('material', 'summary') NOT NULL,
    item_id INT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bookmark_id) REFERENCES bookmarks(id)
        ON DELETE CASCADE
    -- 다형적 연결이라 FK 미지정
);

-- 루시노트 연결용 mysql계정 생성
CREATE USER 'lucinote_conn'@'localhost' IDENTIFIED BY 'elucidateWorld!@#$1234';
-- ② 특정 DB에 대한 권한 부여
GRANT ALL PRIVILEGES ON lucinotedb.* TO 'lucinote_conn'@'localhost';
-- ③ 변경 사항 적용
FLUSH PRIVILEGES;