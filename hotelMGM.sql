CREATE DATABASE hotel;

USE hotel;

desc room;

CREATE TABLE customer (
	c_id INT PRIMARY KEY,
    c_name VARCHAR(60) NOT NULL,
    address VARCHAR(100) NOT NULL,
    checkin DATE NOT NULL,
    checkout DATE NOT NULL,
    gender VARCHAR(1) NOT NULL,
    age INT NOT NULL,
    plan VARCHAR(2)
);

ALTER TABLE customer ADD COLUMN plan VARCHAR(2);
ALTER TABLE customer MODIFY COLUMN paid INT NOT NULL DEFAULT 0;

CREATE TABLE room (
	room_id INT PRIMARY KEY,
    room_type VARCHAR(2) NOT NULL,
    tariff INT NOT NULL,
	upgrade VARCHAR(2) NOT NULL
); 

ALTER TABLE room MODIFY COLUMN room_type VARCHAR(2) NOT NULL;

INSERT INTO room ()
VALUES
(2001, "np", 400, "nu"),
(2002, "s", 600, "up"),
(2003, "s", 600, "up"),
(2004, "c", 500, "nu");


CREATE TABLE booking (
	book_id VARCHAR(5) PRIMARY KEY,
    guest_id INT NOT NULL,
    room_id INT NOT NULL,
    tariff INT NOT NULL,
    service INT NOT NULL,
    discount INT NULL,
    FOREIGN KEY (guest_id) REFERENCES customer(c_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES room(room_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (service) REFERENCES services(service_package)
    ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE services (
	service_package INT PRIMARY KEY,
    service_name VARCHAR(40),
    catering VARCHAR(1),
    tour VARCHAR(1),
    massage VARCHAR(1),
    snacks VARCHAR(1),
    tariff INT NOT NULL
);

INSERT INTO services (service_package, service_name, catering, tour, massage, snacks, tariff)
VALUES
(3001, "Catering", "y", "n", "n", "n", 500),
(3002, "Full", "y", "y", "y","y", 4500),
(3003, "Evening Stay", "n", "y", "n", "y", 1400),
(3004, "None", "n", "n", "n", "n", 0);

################################################# VIEWS ##########################################

CREATE VIEW bill AS 
SELECT 
	c_id AS `customer id`,
    c_name AS `customer name`,
    booking.room_id as `room id`,
    room.room_type AS `room type`,
    room.tariff AS `tariff`,
    checkin AS `check in`,
    checkout AS `check out`,
    DATEDIFF(checkout, checkin) AS `stay`,
    booking.tariff + (room.tariff)*(DATEDIFF(checkout, checkin)) + services.tariff AS `total fare`,
    discount AS `discount`,
    service_package AS `services`,
    (booking.tariff+(room.tariff)*(DATEDIFF(checkout, checkin))+services.tariff) - (discount/100)*(booking.tariff+(room.tariff)*(DATEDIFF(checkout, checkin))+services.tariff) AS `payable`
FROM booking, room, customer, services
WHERE booking.guest_id = customer.c_id AND booking.room_id = room.room_id AND booking.service = services.service_package;


SELECT * FROM bill;
CREATE VIEW service_alloted AS
SELECT 
	c_id AS `customer id`,
    c_name AS `customer name`,
    booking.room_id AS `room id`,
    service_package AS `service package`,
    catering AS `catering`,
    tour AS `tour`,
    massage AS `massage`,
    snacks AS `snacks`
FROM booking, customer, services
WHERE  booking.guest_id = customer.c_id AND booking.service = services.service_package;

CREATE VIEW customer_list AS
SELECT
	c_id AS `customer id`,
    c_name AS `customer name`,
    age AS `age`,
    booking.room_id AS `room id`,
    service_package AS `service package`,
    service_name AS `service name`,
    address AS `address`,
    checkin AS `check in`,
    checkout AS `check out`,
    round((checkout-checkin), 0) AS `stay`,
    upgration AS `upgrade`
FROM customer, room, booking, services
WHERE  booking.guest_id = customer.c_id AND booking.room_id = room.room_id AND booking.service = services.service_package;

CREATE VIEW av_room AS 
SELECT
	room.room_id AS `room id`,
    checkin AS `check in`,
    checkout AS `check out`,
    room.room_type AS `room type`,
    room.tariff AS `tariff`
FROM customer, room, booking
WHERE booking.guest_id = customer.c_id AND booking.room_id = room.room_id;

SELECT * FROM av_room;
SELECT * FROM service_alloted;
SELECT * FROM customer_list;
SELECT * FROM bill;

####################################### INSERTION OF DATA ####################################

INSERT INTO CUSTOMER (c_id, c_name, address, checkin, checkout, gender, age, plan)
VALUES
(1001, "Daksh", "bharat", "2023-12-20", "2023-12-25", "M", 19, "np"),
(1002, "Rahul", "bharat", "2023-12-22", "2023-12-26", "M", 19, "b"),
(1003, "Divyansh", "bharat", "2024-01-04", "2024-01-06","M", 20, "t");


INSERT INTO booking (book_id, guest_id, room_id, tariff, service, discount) 
VALUES
(5001, 1001, 2001, 1000, 3002, 10),
(5002, 1002, 2002, 1000, 3001, 12),
(5003, 1003, 2001, 1000, 3004, 10);

##################################### TRUNCATE OR UPDATE TABLE ######################

SET FOREIGN_KEY_CHECKS = 0;
SET SQL_SAFE_UPDATES = 0;
TRUNCATE TABLE customer;
SET FOREIGN_KEY_CHECKS = 1;
SET SQL_SAFE_UPDATES = 1;

##################################### USER QUERIES ###################################

SELECT room_id, count(guest_id)
FROM booking
GROUP BY room_id;

SELECT * FROM bill
WHERE `check in` > '2024-01-01';

SELECT customer_list.`customer id`, customer_list.`customer name`, `payable`
FROM customer_list, bill
WHERE customer_list.`customer id` = bill.`customer id`
AND customer_list.`customer name` LIKE "%s%"
ORDER BY `payable` ASC;


SELECT checkin FROM customer WHERE c_id = 1003;
SELECT room_id, tariff FROM booking WHERE guest_id = 1003;


SELECT room_type FROM room WHERE room_id = 2001;
SELECT address, gender, IFNULL(paid,0) from customer where c_id=1002;
