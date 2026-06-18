-- ============================================================
-- 初中语文教师智能体 - 数据库初始化脚本
-- 数据库: chinese_teacher
-- 说明: 单用户使用，包含对话列表和对话消息两张表
-- ============================================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS chinese_teacher
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE chinese_teacher;

-- ------------------------------------------------------------
-- 1. 对话列表表 (conversations)
-- ------------------------------------------------------------
DROP TABLE IF EXISTS conversation_messages;
DROP TABLE IF EXISTS conversations;

CREATE TABLE conversations (
    id              BIGINT UNSIGNED     AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    title           VARCHAR(200)        NOT NULL DEFAULT '新对话' COMMENT '对话标题',
    status          TINYINT             NOT NULL DEFAULT 0 COMMENT '状态: 0=活跃, 1=删除',
    create_time     DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    modify_time     DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',

    INDEX idx_status_modify (status, modify_time DESC) COMMENT '按状态和修改时间查询'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话列表表';


-- ------------------------------------------------------------
-- 2. 对话消息记录表 (conversation_messages)
-- ------------------------------------------------------------
CREATE TABLE conversation_messages (
    id                  BIGINT UNSIGNED     AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    conversation_id     BIGINT UNSIGNED     NOT NULL COMMENT '所属对话ID',
    role                TINYINT             NOT NULL COMMENT '说话人: 0=用户, 1=AI助手, 2=系统提示',
    content             LONGTEXT            NOT NULL COMMENT '消息内容',
    create_time         DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    -- 外键约束
    CONSTRAINT fk_msg_conversation
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    INDEX idx_conversation_created (conversation_id, create_time ASC) COMMENT '按对话ID和时间顺序查询'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话消息记录表';
