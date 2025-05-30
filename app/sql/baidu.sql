/*
 Navicat Premium Data Transfer

 Source Server         : 8.138.177.105
 Source Server Type    : MySQL
 Source Server Version : 80042 (8.0.42)
 Source Host           : 8.138.177.105:3306
 Source Schema         : baidu

 Target Server Type    : MySQL
 Target Server Version : 80042 (8.0.42)
 File Encoding         : 65001

 Date: 30/05/2025 23:44:33
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for words
-- ----------------------------
DROP TABLE IF EXISTS `words`;
CREATE TABLE `words`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `words` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '敏感词',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of words
-- ----------------------------

SET FOREIGN_KEY_CHECKS = 1;
