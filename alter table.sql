USE onlineairticketreservationsystem;

ALTER TABLE ticket
ADD customer_email VARCHAR(30) NOT NULL,
ADD booking_agent_email VARCHAR(30),  -- 默认允许 NULL
ADD CONSTRAINT fk_customer_email
    FOREIGN KEY (customer_email) REFERENCES customer(email),
ADD CONSTRAINT fk_booking_agent_email
    FOREIGN KEY (booking_agent_email) REFERENCES booking_agent(email);


DELETE FROM airplane;



UPDATE customer SET password = MD5(password);
UPDATE customer SET password = MD5(password) WHERE email = 'kkw2001@gmail.com'

Update booking_agent SET password = MD5(password);
UPDATE airline_staff SET password = MD5(password);

update airline_staff set password = MD5(password) where username = "Jenny_2";
update airline_staff set password = MD5(password) where username = "Amelia_3";


delete from permission 
where username = 'Jenny_2' and permission_type= 'ADMIN';
delete from permission where username = 'Vivian_1' and permission_type= 'Operator';
UPDATE purchases
SET ticket_id = 105
WHERE customer_email = 'aliceW@gmail.com';

ALTER TABLE customer
ADD COLUMN balance DECIMAL(10, 2) DEFAULT 0.00;

UPDATE customer
SET balance = 25670.00
WHERE email = 'aliceW@gmail.com';

UPDATE customer
SET balance = 10000.00
WHERE email = 'ht2604@nyu.edu';


UPDATE flight
SET status = 'upcoming'
WHERE flight_num = 463 AND airline_name = 'China Eastern';

ALTER TABLE ticket MODIFY ticket_id INT NOT NULL AUTO_INCREMENT;
#一定要改

delete from booking_agent_work_for where email = 'xiaozhou@qq.com'