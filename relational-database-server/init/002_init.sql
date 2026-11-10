CREATE DATABASE IF NOT EXISTS studentdb;
USE studentdb;
CREATE TABLE IF NOT EXISTS students(
  id INT PRIMARY KEY AUTO_INCREMENT,
  student_id VARCHAR(10),
  fullname VARCHAR(100),
  dob DATE,
  major VARCHAR(50)
);
INSERT INTO students(student_id, fullname, dob, major) VALUES
 ('SV001','Nguyễn Văn A','2004-01-15','CNTT'),
 ('SV002','Trần Thị B','2004-05-20','Mạng máy tính'),
 ('SV003','Lê Văn C','2003-11-02','An toàn thông tin');