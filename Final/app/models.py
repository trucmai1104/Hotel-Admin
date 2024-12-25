from datetime import datetime
from multiprocessing.connection import address_type

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Enum, DateTime, Table
from sqlalchemy.orm import relationship, backref
from app import db, app
from enum import Enum as RoleEnum
from flask_login import UserMixin

class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, nullable=False, autoincrement=True, primary_key=True)

####CÁC BẢNG TRUNG GIAN####

ReservationCustomer = db.Table(
    'ReservationCustomer',
    Column('reservation_id', Integer, ForeignKey('Reservation.id'), primary_key=True),
    Column('customer_id', Integer, ForeignKey('Customer.id'), primary_key=True)
)

CustomerRoomRental = db.Table(
    'CustomerRoomRental',
    Column('customer_id', Integer, ForeignKey('Customer.id'), primary_key=True),
    Column('room_rental_id', Integer, ForeignKey('RoomRental.id'), primary_key=True)
)

####CÁC BẢNG TRUNG GIAN####


class UserRole(RoleEnum):
    ADMIN = 1
    CUSTOMER = 2
    RECEPTION = 3

class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=True)
    phone = Column(String(50), nullable=True, unique=True)
    gender = Column(Boolean, default=True)  # True = 1 is 'Man'
    avatar = Column(String(100),
                    default='https://res.cloudinary.com/dxxwcby8l/image/upload/v1646729533/zuur9gzztcekmyfenkfr.jpg')
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER)

class Administrator(db.Model):
    id = Column(Integer, ForeignKey(User.id), nullable=False, primary_key=True)
    name = Column(String(50), nullable=False)


class Receptionist(db.Model):
    id = Column(Integer, ForeignKey(User.id), nullable=False, primary_key=True)
    name = Column(String(50), nullable=False)
    reservations = relationship('Reservation', backref='receptionist', lazy=True)
    room_rentals = relationship('RoomRental', backref='receptionist', lazy=True)

class CustomerType(RoleEnum):
    DOMESTIC = 1
    FOREIGN = 2

class Customer(BaseModel):
    __tablename__ = 'Customer'
    name = Column(String(100), nullable=False)
    customer_type = Column(Enum(CustomerType), default=CustomerType.DOMESTIC)
    cmnd = Column(String(100), nullable=False)
    address = Column(String(500), nullable=False)
    comments = relationship('Comment', lazy=True)

    # Mối quan hệ với RoomRental thông qua bảng trung gian
    room_rentals = relationship('RoomRental',
                                secondary=CustomerRoomRental,  # Updated to PascalCase
                                backref=backref('customers', lazy='subquery'),
                                lazy='subquery')

class RoomType(BaseModel):
    __tablename__ = 'RoomType'
    name = Column(String(50), nullable=False, unique=True)
    rooms = relationship('Room', backref='room_type', lazy=True)

    def __str__(self):
        return self.name

class Room(BaseModel):
    __tablename__ = 'Room'
    name = Column(String(100), nullable=False, unique=True)
    image = Column(String(500), default='static/images/phong1.jpg')
    room_type_id = Column(Integer, ForeignKey('RoomType.id'), nullable=False)
    status = Column(String(100), nullable=True)
    room_rentals = relationship('RoomRental', backref='room', lazy='subquery')
    reservation = relationship('Reservation', backref='room', lazy='subquery')
    comments = relationship('Comment', lazy=True)

    def __str__(self):
        return self.name

class RoomRental(BaseModel):
    __tablename__ = 'RoomRental'
    room_id = Column(Integer, ForeignKey('Room.id'), nullable=False)
    receptionist_id = Column(Integer, ForeignKey(Receptionist.id), nullable=False)
    checkin_date = Column(DateTime, nullable=False)
    checkout_date = Column(DateTime, nullable=False)
    deposit = Column(Float)
    is_paid = Column(Boolean, default=False)
    receipt_id = relationship('Receipt', backref='room', lazy='subquery')


class Reservation(BaseModel):
    __tablename__ = 'Reservation'
    room_id = Column(Integer, ForeignKey('Room.id'), nullable=False)
    receptionist_id = Column(Integer, ForeignKey(Receptionist.id))
    checkin_date = Column(DateTime)
    checkout_date = Column(DateTime)
    booker_name = Column(String(100), nullable=False)
    is_checkin = Column(Boolean, default=False)
    deposit = Column(Float, nullable=False)
    # Mối quan hệ Many-to-Many với Customer
    customers = relationship('Customer',
                             secondary=ReservationCustomer,  # Updated to PascalCase
                             backref=backref('reservations', lazy='subquery'),
                             lazy='subquery')

class Receipt(BaseModel):
    receptionist_id = Column(Integer, ForeignKey(Receptionist.id), nullable=False)
    rental_room_id = Column(Integer, ForeignKey(RoomRental.id), nullable=False, primary_key=True)
    total_price = Column(Float, nullable=False)
    created_date = Column(DateTime, nullable=False, default=datetime.now())

class Comment(BaseModel):
    customer_id = Column(Integer, ForeignKey('Customer.id'), nullable=False, primary_key=True)
    content = Column(String(1000), nullable=False)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False, primary_key=True)
    created_date = Column(DateTime, default=datetime.now())

class CustomerTypeRegulation(BaseModel):
    __tablename__ = 'CustomerTypeRegulation'
    rate = Column(Float, default=1.0, nullable=False)
    admin_id = Column(Integer, ForeignKey(Administrator.id), nullable=False)
    customer_type = Column(Enum(CustomerType), default=CustomerType.DOMESTIC)

class RoomTypeRegulation(BaseModel):
    __tablename__ = 'RoomTypeRegulation'
    room_type_id = Column(Integer, ForeignKey('RoomType.id'), nullable=False)
    room_quanity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    admin_id = Column(Integer, ForeignKey(Administrator.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now())

class RoomCustomerRegulation(BaseModel):
    __tablename__ = 'RoomCustomerRegulation'
    room_type_id = Column(Integer, ForeignKey('RoomType.id'), nullable=False)
    max_customers = Column(Integer, nullable=False, default=3)  # Số khách tối đa/phòng
    admin_id = Column(Integer, ForeignKey(Administrator.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now())

class SurchargeRegulation(BaseModel):
    __tablename__ = 'SurchargeRegulation'
    default_customer_count = Column(Integer, default=2)  # Mặc định 2 người
    surcharge_rate = Column(Float, default=0.25)  # Phụ thu 25% cho người thứ 3
    admin_id = Column(Integer, ForeignKey(Administrator.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now())

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        db.session.commit()

        # rt1 = RoomType(name='VIP')
        # rt2 = RoomType(name='DELUXE')
        # rt3 = RoomType(name='STANDARD')
        # db.session.add_all([rt1, rt2, rt3])
        # db.session.commit()

        # r1 = Room(name='101', room_type_id=2, image='https://res.cloudinary.com/dglrht3fj/image/upload/v1734602365/3_pqzxfn.jpg')
        # r2 = Room(name='202', room_type_id=3, image='https://res.cloudinary.com/dglrht3fj/image/upload/v1734602365/2_huy4nn.jpg')
        # r3 = Room(name='303', room_type_id=1, image='https://res.cloudinary.com/dglrht3fj/image/upload/v1734602365/11_xzzop2.jpg')
        # r4 = Room(name='404', room_type_id=1, image='https://res.cloudinary.com/dglrht3fj/image/upload/v1734602366/8_xvwisw.jpg')
        # r5 = Room(name='505', room_type_id=3, image='https://res.cloudinary.com/dglrht3fj/image/upload/v1734602366/8_xvwisw.jpg')
        # db.session.add_all([r1, r2, r3, r4, r5])
        # db.session.commit()

        # import hashlib
        #
        # user1 = User(
        #     role=UserRole.ADMIN,
        #     username='trucmai',
        #     name = 'Trần Thị Trúc Mai',
        #     password=str(hashlib.md5('123'.encode('utf-8')).hexdigest()),
        #     avatar='https://res.cloudinary.com/dglrht3fj/image/upload/v1732380539/kctr5oorhhm1nxp2na98.jpg',
        #     email='mai@gmail.com',
        #     phone='0334454203',
        #     gender=False)
        # user2 = User(
        #     role=UserRole.ADMIN,
        #     name = 'Nguyễn Thiện Đoan',
        #     username='doan',
        #     password=str(hashlib.md5('doan'.encode('utf-8')).hexdigest()),
        #     avatar='https://res.cloudinary.com/dglrht3fj/image/upload/v1732380539/kctr5oorhhm1nxp2na98.jpg',
        #     email='doan@gmail.com',
        #     phone='0869311727')
        # user3 = User(
        #     role=UserRole.ADMIN,
        #     name = 'Nguyễn Hải Đăng',
        #     username='dang',
        #     password=str(hashlib.md5('dang'.encode('utf-8')).hexdigest()),
        #     avatar='https://res.cloudinary.com/dglrht3fj/image/upload/v1732380539/kctr5oorhhm1nxp2na98.jpg',
        #     email='dang@gmail.com',
        #     phone='0123456789')
        # user4 = User(
        #     role=UserRole.CUSTOMER,
        #     name = 'Trần Thị Lan',
        #     username='lan',
        #     password=str(hashlib.md5('lan'.encode('utf-8')).hexdigest()),
        #     avatar='https://res.cloudinary.com/dglrht3fj/image/upload/v1732380539/kctr5oorhhm1nxp2na98.jpg',
        #     email='lan@gmail.com',
        #     phone='0642138713',
        #     gender=False)
        # user5 = User(
        #     role=UserRole.CUSTOMER,
        #     name = 'Hồ Minh Tuân',
        #     username='tuan',
        #     password=str(hashlib.md5('tuan'.encode('utf-8')).hexdigest()),
        #     avatar='https://res.cloudinary.com/dglrht3fj/image/upload/v1732380539/kctr5oorhhm1nxp2na98.jpg',
        #     email='tuan@gmail.com',
        #     phone='0287112946')
        # user6 = User(
        #     role=UserRole.CUSTOMER,
        #     name = 'Trần Minh Kiệt',
        #     username='kiet',
        #     password=str(hashlib.md5('lau'.encode('utf-8')).hexdigest()),
        #     avatar='https://res.cloudinary.com/dglrht3fj/image/upload/v1732380539/kctr5oorhhm1nxp2na98.jpg',
        #     email='kiet@gmail.com',
        #     phone='0198247172')
        #
        # user7 = User(
        #     username='LeTan',
        #     name = 'Trần Thị Lệ Tấn',
        #     password=str(hashlib.md5('123'.encode('utf-8')).hexdigest()),
        #     role=UserRole.RECEPTION,
        #     email='letan@gmail.com',
        #     phone='035588475',
        #     gender=False)
        # db.session.commit()
        # db.session.add_all([user1, user2, user3, user4, user5, user6, user7])
        # db.session.commit()
        # admin1= Administrator(id=2, name='Nguyên Thện Đoan')
        # db.session.add(admin1)
        # db.session.commit()

        # r1 = Receptionist(name='Trần Thị Lệ Tấn', id=7)
        # db.session.add(r1)
        # db.session.commit()

        # cus1 = Customer(id=4, name='Trần Thị Lan', cmnd='0194612374612', customer_type = CustomerType.DOMESTIC, address='Hồ Chí Minh')
        # cus2 = Customer(id=5, name='Hồ Minh Tuân', cmnd='0123491958123', customer_type = CustomerType.FOREIGN, address = 'England')
        # cus3 = Customer(id=6, name='Trần Minh Kiệt', cmnd='01235012357', customer_type = CustomerType.DOMESTIC, address = 'An Giang')
        # db.session.add_all([cus1, cus2, cus3])
        # db.session.commit()

        # ctr1 = CustomerTypeRegulation(admin_id=1)
        # ctr2 = CustomerTypeRegulation(admin_id=1, customer_type = CustomerType.FOREIGN, rate=1.5)
        # db.session.add_all([ctr1, ctr2])
        # db.session.commit()
        #
        # rr1 = RoomTypeRegulation(room_type_id=1, admin_id=1, room_quanity=10, price=3000000)
        # rr2 = RoomTypeRegulation(room_type_id=2, admin_id=1, room_quanity=15,  price=4000000)
        # rr3 = RoomTypeRegulation(room_type_id=3, admin_id=1, room_quanity=17,  price=5000000)
        # db.session.add_all([rr1, rr2, rr3])
        # db.session.commit()

        # cm1 = Comment(customer_id=4, content='Phòng này quá ok <3', room_id=1, created_date=datetime(2024, 1, 9, 17, 1))
        # cm2 = Comment(customer_id=6, content='Cũng tàm tạm, cần nâng cấp dịch vụ phòng!',
        #               created_date=datetime(2024, 1, 9, 17, 1), room_id=1)
        # cm3 = Comment(customer_id=5, content='Sẽ ghé thăm vào lần sau nếu có dịp',
        #               created_date=datetime(2024, 1, 9, 17, 1), room_id=2)
        # cm4 = Comment(customer_id=6, content='Một căn phòng đáng trải nghiệm nhất tại khách sạn, 5 sau nhé',
        #               created_date=datetime(2024, 1, 9, 17, 1), room_id=2)
        # cm5 = Comment(customer_id=4,
        #               content='Mình có một người bạn nước ngoài ở chung, sẽ nhân hệ số 1.5 nhưng đây là quy định chung của khách sạn rùi nên cũng không sao, miễn là dịch vụ OK và phòng thì miễn chê',
        #               created_date=datetime(2024, 1, 9, 17, 1),
        #               room_id=2)
        # cm6 = Comment(customer_id=5,
        #               content='Có dịp ghé qua đây, đang loay hoay tìm phòng thì có dịch vụ đặt phòng trước, đến nơi chỉ cần đưa thông tin phiếu cho nhân viên lễ tân là nhận phòng ở luôn, 10 điểm',
        #               created_date=datetime(2024, 1, 9, 17, 1),
        #               room_id=3)
        #
        # db.session.add_all([cm1, cm2,
        #                     cm3, cm4, cm5, cm6,
        #                     ])
        # db.session.commit()

        # reservation = Reservation(
        #     room_id=2,
        #     receptionist_id=7,
        #     checkin_date=datetime(2024, 6, 19, 19, 0, 0),  # Ngày giờ check-in
        #     checkout_date=datetime(2024, 7, 20, 12, 0, 0),  # Ngày giờ check-out
        #     booker_name="Trần Minh Kiệt",
        #     is_checkin=False,
        #     deposit=700000,
        # )
        #
        # customer1 = db.session.query(Customer).filter_by(id=6).first()
        # reservation.customers = [customer1]
        #
        # db.session.add(reservation)
        # db.session.commit()

        # room_rental1 = RoomRental(
        #     receptionist_id=7,
        #     room_id=4,
        #     checkin_date=datetime(2024, 1, 17, 20, 55, 32),
        #     checkout_date=datetime(2024, 1, 29, 20, 55, 32),
        #     deposit=None,
        #     is_paid=True
        # )
        #
        # room_rental2 = RoomRental(
        #     receptionist_id=7,
        #     room_id=2,
        #     checkin_date=datetime(2024, 2, 1, 20, 55, 32),
        #     checkout_date=datetime(2024, 2, 18, 20, 55, 32),
        #     deposit=None,
        #     is_paid=True
        # )
        #
        # room_rental3 = RoomRental(
        #     receptionist_id=7,
        #     room_id=3,
        #     checkin_date=datetime(2024, 2, 3, 20, 55, 32),
        #     checkout_date=datetime(2024, 2, 26, 20, 55, 32),
        #     deposit=1500000,
        #     is_paid=True
        # )
        #
        # room_rental4 = RoomRental(
        #     receptionist_id=7,
        #     room_id=2,
        #     checkin_date=datetime(2024, 2, 27, 20, 55, 32),
        #     checkout_date=datetime(2024, 3, 5, 20, 55, 32),
        #     deposit=None,
        #     is_paid=True
        # )
        #
        # room_rental5 = RoomRental(
        #     receptionist_id=7,
        #     room_id=1,
        #     checkin_date=datetime(2023, 8, 3, 20, 55, 32),
        #     checkout_date=datetime(2024, 8, 24, 20, 55, 32),
        #     deposit=None,
        #     is_paid=True
        # )
        #
        # # Thêm các đối tượng vào cơ sở dữ liệu
        # with db.session.begin():
        #     db.session.add_all(
        #         [room_rental1, room_rental2, room_rental3, room_rental4, room_rental5])
        #
        # # Lưu thay đổi vào cơ sở dữ liệu
        # db.session.commit()

        # receipt_data = [
        #             {'receptionist_id': 7, 'rental_room_id': 10, 'total_price': 3000000, 'created_date': datetime(2023, 1, 19, 17, 1)},
        #             {'receptionist_id': 7, 'rental_room_id': 1, 'total_price': 5000000, 'created_date': datetime(2023, 1, 29, 17, 11)},
        #             {'receptionist_id': 7, 'rental_room_id': 2, 'total_price': 5000000, 'created_date': datetime(2023, 2, 19, 17, 11)},
        #             {'receptionist_id': 7, 'rental_room_id': 3, 'total_price': 5000000, 'created_date': datetime(2023, 4, 29, 17, 11)},
        #             {'receptionist_id': 7, 'rental_room_id': 4, 'total_price': 4000000, 'created_date': datetime(2024, 1, 29, 17, 11)},
        #             {'receptionist_id': 7, 'rental_room_id': 5, 'total_price': 4000000, 'created_date': datetime(2024, 2, 29, 17, 11)},
        #             ]
        #
        # for data in receipt_data:
        #     receipt = Receipt(**data)
        #     db.session.add(receipt)
        #
        # db.session.commit()
        # s = SurchargeRegulation(admin_id=1)
        # db.session.add(s)
        # db.session.commit()