import hashlib
import hmac
import threading
import urllib
from datetime import datetime

from flask_login import current_user, AnonymousUserMixin
from sqlalchemy import func, Numeric, extract, or_, and_, case, desc, text
from sqlalchemy.orm import aliased

from app.models import *
from app import app, utils

import smtplib


def send_message_twilio(message):
    from twilio.rest import Client

    account_sid = 'AC34dbe9c496f4108ac74cda4a50ab4b94'
    auth_token = '112ca59ebefd2a224813f7339cf368aa'
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        from_='+17178976092',
        body=str(message),
        to='+84869311727'
    )




def get_room_types():
    with app.app_context():
        room_types = RoomType.query.all()
        return room_types


def get_user_by_id(user_id=None):
    with app.app_context():
        user = User.query.get(id)
        return user


def get_rooms():
    with app.app_context():
        rooms = Room.query.all()
        return rooms


def auth_user(username, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

    return User.query.filter(User.username.__eq__(username.strip()),
                             User.password.__eq__(password)).first()



def get_room_type_regulation():
    # if current_user.is_authenticated and current_user.role.__eq__(UserRole.ADMIN):
    with app.app_context():
        room_type_regulation = db.session.query(RoomType.name.label('rome_type_name'),
                                           User.username.label('user_name'),
                                           RoomTypeRegulation.room_quanity,
                                           RoomTypeRegulation.price) \
            .join(Administrator, Administrator.id == RoomTypeRegulation.admin_id) \
            .join(RoomType, RoomType.id == RoomTypeRegulation.room_type_id) \
            .join(User, User.id == Administrator.id)

        return room_type_regulation.all()


def get_customer_type_regulation():
    # if current_user.is_authenticated and current_user.role.__eq__(UserRole.ADMIN):
    with app.app_context():
        customer_type_regulation = db.session.query(CustomerTypeRegulation.id,
                                                    CustomerTypeRegulation.customer_type,
                                                    Administrator.name.label('name_admin'),
                                                    CustomerTypeRegulation.rate) \
            .join(Administrator, Administrator.id == CustomerTypeRegulation.admin_id)  \
            .group_by(CustomerTypeRegulation.id,
                      CustomerTypeRegulation.customer_type,
                      Administrator.name.label('name_admin'),
                      CustomerTypeRegulation.rate) \
            .all()

        # print(customer_type_regulation)
        return customer_type_regulation

def get_surcharge_regulation():
    # if current_user.is_authenticated and current_user.role.__eq__(UserRole.ADMIN):
    with app.app_context():
        surcharge_regulation = db.session.query(SurchargeRegulation.id,
                                                    SurchargeRegulation.surcharge_rate,
                                                    Administrator.name.label('name_admin'),
                                                    SurchargeRegulation.default_customer_count,) \
            .join(Administrator, Administrator.id == SurchargeRegulation.admin_id) \
            .group_by(SurchargeRegulation.id,
                      SurchargeRegulation.surcharge_rate,
                      Administrator.name.label('name_admin'),
                      SurchargeRegulation.default_customer_count) \
            .all()

        return surcharge_regulation


def month_sale_statistic(month=None, year=None, kw=None, from_date=None, to_date=None, **kwargs):
    with app.app_context():
        if not kw and not from_date and not to_date and not month and not year:
            count_receipt = Receipt.query.count()
        elif from_date:
            count_receipt = Receipt.query.filter(
                Receipt.created_date.__ge__(from_date)).count()
        elif to_date:
            count_receipt = Receipt.query.filter(
                Receipt.created_date.__le__(to_date)).count()
        elif kw:
            count_receipt = Receipt.query.count()
        elif month:
            count_receipt = Receipt.query.filter(
                extract('month', Receipt.created_date) == month)
            if year:
                count_receipt = count_receipt.filter(
                    extract('year', Receipt.created_date) == year)
            count_receipt = count_receipt.count()
        else:
            count_receipt = Receipt.query.filter(
                extract('year', Receipt.created_date) == year).count()

        month_sale_statistic = db.session.query(RoomType.name,
                                                func.coalesce(func.sum(Receipt.total_price), 0),
                                                func.coalesce(func.count(Receipt.id), 0),
                                                func.cast((func.count(Receipt.id) / count_receipt) * 100
                                                          , Numeric(5, 2))) \
            .join(Room, Room.room_type_id.__eq__(RoomType.id), isouter=True) \
            .join(RoomRental, RoomRental.room_id.__eq__(Room.id), isouter=True) \
            .join(Receipt, Receipt.rental_room_id.__eq__(RoomRental.id), isouter=True) \
            .group_by(RoomType.name) \
            .order_by(RoomType.id)

        if month:
            month_sale_statistic = month_sale_statistic.filter(
                extract('month', Receipt.created_date) == month)

        if year:
            month_sale_statistic = month_sale_statistic.filter(
                extract('year', Receipt.created_date) == year)

        if kw:
            month_sale_statistic = month_sale_statistic.filter(
                RoomType.name.contains(kw))

        if from_date:
            month_sale_statistic = month_sale_statistic.filter(
                Receipt.created_date.__ge__(from_date))

        if to_date:
            month_sale_statistic = month_sale_statistic.filter(
                Receipt.created_date.__le__(to_date))

        return month_sale_statistic.all()


def room_utilization_report(month=None, year=None, room_name=None, **kwargs):
    with app.app_context():
        checkout_date_column = RoomRental.checkout_date  # Định rõ cột 'checkout_date' để sử dụng trong câu truy vấn

        room_rental = RoomRental.query
        if month and year and room_name:
            room_rental = room_rental.join(Room, Room.id.__eq__(RoomRental.room_id)) \
                .filter(extract('month', checkout_date_column) == month and
                        extract('year', checkout_date_column) == year and
                        Room.name.__eq__(room_name))
        elif month:
            room_rental = room_rental.filter(extract('month', checkout_date_column) == month)
            if year:
                room_rental = room_rental.filter(extract('year', checkout_date_column) == year)
        elif year:
            room_rental = room_rental.filter(extract('year', checkout_date_column) == year)

        count = room_rental.count()

        result = db.session.query(
            Room.name,
            func.sum(func.datediff(RoomRental.checkout_date, RoomRental.checkin_date)),
            func.cast((func.count() / count) * 100
                      , Numeric(5, 2))
        ).join(RoomRental, RoomRental.room_id.__eq__(Room.id)).group_by(Room.name).order_by(Room.id)

        if month:
            # Thống kê theo tháng
            result = result.filter(extract('month', checkout_date_column) == month)
        if year:
            # Thống kê theo năm
            result = result.filter(extract('year', checkout_date_column) == year)
        if room_name:
            # Thống kê theo tên phòng
            result = result.filter(Room.name == room_name)

        return result.all()
