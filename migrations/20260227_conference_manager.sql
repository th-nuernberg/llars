-- Conference Manager Schema
-- Creates tables for conference tracking and paper management

-- Conferences table
CREATE TABLE IF NOT EXISTS conferences (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    acronym VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    core_ranking ENUM('A*','A','B','C','Unranked') NOT NULL DEFAULT 'Unranked',
    submission_deadline DATETIME NULL,
    notification_date DATETIME NULL,
    start_date DATETIME NULL,
    end_date DATETIME NULL,
    city VARCHAR(255) NULL,
    country VARCHAR(255) NULL,
    website_url VARCHAR(2048) NULL,
    keywords JSON NULL,
    notes TEXT NULL,
    created_by VARCHAR(255) NOT NULL,
    updated_by VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_conference_year (acronym, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Papers table
CREATE TABLE IF NOT EXISTS papers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(500) NOT NULL,
    status ENUM('planning','in_progress','submitted','accepted','rejected') NOT NULL DEFAULT 'planning',
    conference_id INT NULL,
    overleaf_url VARCHAR(2048) NULL,
    external_url VARCHAR(2048) NULL,
    keywords JSON NULL,
    description TEXT NULL,
    notes TEXT NULL,
    created_by VARCHAR(255) NOT NULL,
    updated_by VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_papers_conference FOREIGN KEY (conference_id) REFERENCES conferences(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paper authors table
CREATE TABLE IF NOT EXISTS paper_authors (
    id INT PRIMARY KEY AUTO_INCREMENT,
    paper_id INT NOT NULL,
    user_id INT NULL,
    external_name VARCHAR(255) NULL,
    author_order INT NOT NULL DEFAULT 0,
    is_corresponding BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_paper_authors_paper FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
    CONSTRAINT fk_paper_authors_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE KEY unique_paper_user (paper_id, user_id),
    CONSTRAINT chk_author_identity CHECK (user_id IS NOT NULL OR external_name IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Indexes for common queries
CREATE INDEX idx_conferences_year ON conferences(year);
CREATE INDEX idx_conferences_deadline ON conferences(submission_deadline);
CREATE INDEX idx_papers_status ON papers(status);
CREATE INDEX idx_papers_conference ON papers(conference_id);
CREATE INDEX idx_paper_authors_paper ON paper_authors(paper_id);
CREATE INDEX idx_paper_authors_user ON paper_authors(user_id);
