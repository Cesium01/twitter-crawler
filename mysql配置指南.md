mysql配置
====
前置工作
----
1. [安装](https://dev.mysql.com/downloads/mysql/)  
2. [基础语法](https://www.runoob.com/mysql/mysql-tutorial.html)  
3. 启动mysql服务
`net start mqsql`  
**注意：Windows系统需以管理员模式启动cmd**
4. 设置数据库用户信息并登录

建立数据库
----
```mysql
CREATE DATABASE TWITTER;
```
建立数据表
----
```mysql
USE TWITTER;
------回车------
CREATE TABLE IF NOT EXIST `followers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` char(8) NOT NULL,
  `nid` bigint DEFAULT NULL,
  `usrid` char(30) NOT NULL,
  `latest` char(19) NOT NULL,
  `number` int NOT NULL,
  `time` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```  
####字段解释
字段名  | 类型 |Python类型|备注 |
------ | :----:|:------:|:----:|
id     | INT   |  int   ||
name  | CHAR(8) |  str  |自定义的推特用户标识名|
nid   | BIGINT |  int   |推特用户id(一串数字)|
userid| CHAR(30)| str   |推特用户的screen_name|
latest| CHAR(19)| str   |最新推文id|
number| INT    |  int   |关注者数目|
time  |DATETIME|datetime.datetime|记录时间 |
录入推特用户数据
----
**name, userid这两个字段必须设置初始值**
```mysql
INSERT INTO followers
(name,userid,time)
VALUES
("三森铃子","mimori_suzuko",CURRENT_TIMESTAMP()),
("伊波杏树","anju_inami",CURRENT_TIMESTAMP());
```