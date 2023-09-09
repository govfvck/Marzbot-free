from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `users` (
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `username` VARCHAR(200),
    `name` VARCHAR(200),
    `is_blocked` BOOL NOT NULL  DEFAULT 0,
    `super_user` BOOL NOT NULL  DEFAULT 0,
    `force_join_check` DATETIME(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `transactions` (
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `type` SMALLINT NOT NULL  COMMENT 'crypto: 1\nby_admin: 2',
    `status` SMALLINT NOT NULL  COMMENT 'waiting: 1\nfailed: 2\ncanceled: 3\npartially_paid: 4\nfinished: 5' DEFAULT 1,
    `finished_at` DATETIME(6),
    `amount` INT NOT NULL,
    `amount_paid` INT,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_transact_users_6189e5a9` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `byadmin_payments` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `type` SMALLINT NOT NULL  COMMENT 'crypto: 1\nby_admin: 2' DEFAULT 2,
    `by_admin_id` BIGINT,
    `transaction_id` BIGINT NOT NULL UNIQUE,
    CONSTRAINT `fk_byadmin__users_22c9072e` FOREIGN KEY (`by_admin_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_byadmin__transact_617e558f` FOREIGN KEY (`transaction_id`) REFERENCES `transactions` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `crypto_payments` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `type` SMALLINT NOT NULL  COMMENT 'crypto: 1\nby_admin: 2' DEFAULT 1,
    `usdt_rate` INT NOT NULL,
    `invoice_id` VARCHAR(64) NOT NULL,
    `order_id` VARCHAR(64),
    `price_amount` DOUBLE NOT NULL,
    `price_currency` VARCHAR(20) NOT NULL,
    `nowpm_created_at` DATETIME(6),
    `pay_currency` VARCHAR(32),
    `pay_amount` DOUBLE,
    `order_description` VARCHAR(64),
    `nowpm_updated_at` DATETIME(6),
    `payment_status` SMALLINT NOT NULL  COMMENT 'waiting: 0\nconfirming: 1\nconfirmed: 2\nsending: 3\npartially_paid: 4\nfinished: 5\nfailed: 6\nrefunded: 7\nexpired: 8' DEFAULT 0,
    `outcome_amount` DOUBLE,
    `outcome_currency` VARCHAR(20),
    `purchase_id` VARCHAR(64),
    `pay_address` VARCHAR(128),
    `transaction_id` BIGINT NOT NULL UNIQUE,
    CONSTRAINT `fk_crypto_p_transact_d08038fb` FOREIGN KEY (`transaction_id`) REFERENCES `transactions` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `servers` (
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `host` VARCHAR(64) NOT NULL,
    `port` INT,
    `token` VARCHAR(512) NOT NULL,
    `https` BOOL NOT NULL  DEFAULT 0,
    `name` VARCHAR(200),
    `is_enabled` BOOL NOT NULL  DEFAULT 1
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `services` (
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(64) NOT NULL,
    `data_limit` BIGINT NOT NULL,
    `expire_duration` INT NOT NULL,
    `inbounds` JSON NOT NULL,
    `flow` VARCHAR(20)   COMMENT 'none: None\nxtls_rprx_vision: xtls-rprx-vision' DEFAULT 'None',
    `price` INT NOT NULL,
    `one_time_only` BOOL NOT NULL  DEFAULT 0,
    `is_test_service` BOOL NOT NULL  DEFAULT 0,
    `purchaseable` BOOL NOT NULL  DEFAULT 0,
    `renewable` BOOL NOT NULL  DEFAULT 0,
    `server_id` BIGINT NOT NULL,
    CONSTRAINT `fk_services_servers_be0c61a1` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `proxies` (
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `custom_name` VARCHAR(64),
    `username` VARCHAR(32) NOT NULL UNIQUE,
    `cost` INT,
    `status` VARCHAR(12) NOT NULL  COMMENT 'active: active\ndisabled: disabled\nlimited: limited\nexpired: expired' DEFAULT 'active',
    `renewed_at` DATETIME(6),
    `server_id` BIGINT NOT NULL,
    `service_id` INT,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_proxies_servers_43cfb161` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_proxies_services_338cef03` FOREIGN KEY (`service_id`) REFERENCES `services` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_proxies_users_b8af88b7` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    KEY `idx_proxies_usernam_c3e1f3` (`username`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `invoices` (
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `amount` INT NOT NULL,
    `type` SMALLINT NOT NULL  COMMENT 'purchase: 1\nrenew: 2' DEFAULT 1,
    `proxy_id` INT,
    `transaction_id` BIGINT,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_invoices_proxies_dfa62f0f` FOREIGN KEY (`proxy_id`) REFERENCES `proxies` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_invoices_transact_dbab496e` FOREIGN KEY (`transaction_id`) REFERENCES `transactions` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_invoices_users_b9efcef2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `user_purchased` (
    `services_id` INT NOT NULL,
    `user_id` BIGINT NOT NULL,
    FOREIGN KEY (`services_id`) REFERENCES `services` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
