from sqlalchemy import Column, DateTime, String, Integer, Text, Numeric, ForeignKey, func, CheckConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata

class User(Base):
    """Tabel Users"""
    __tablename__ = 'users'
    __table_args__ = (CheckConstraint("role IN ('Customer', 'Admin')", name='check_user_role'),)
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    
    # KOLOM BARU
    phone_number = Column(String(20), nullable=True) 
    
    admin_events = relationship("Event", back_populates="admin")
    bookings = relationship("Booking", back_populates="customer")

    def __repr__(self):
        return f"<User {self.name}>"

class Event(Base):
    """Tabel Events"""
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey('users.id'), nullable=False) 
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    date = Column(DateTime, nullable=False)
    venue = Column(String(255), nullable=False)
    ticket_price = Column(Numeric(10, 2), nullable=False)
    total_capacity = Column(Integer, nullable=False) 

    admin = relationship("User", back_populates="admin_events")
    bookings = relationship("Booking", back_populates="event")
    seats = relationship("Seat", back_populates="event", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Event {self.name}>"

class Booking(Base):
    """Tabel Bookings"""
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    booking_code = Column(String(50), unique=True, nullable=False)
    booking_date = Column(DateTime, default=func.now())
    status = Column(String(20), default='Pending', nullable=False) 

    event = relationship("Event", back_populates="bookings")
    customer = relationship("User", back_populates="bookings")
    payment = relationship("Payment", back_populates="booking", uselist=False)
    seats = relationship("Seat", back_populates="booking")

    def __repr__(self):
        return f"<Booking {self.booking_code}>"

class Seat(Base):
    """Tabel Seats (Kursi)"""
    __tablename__ = 'seats'

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=True)
    
    seat_label = Column(String(10), nullable=False) # Contoh: A1, B2
    is_booked = Column(Boolean, default=False)

    event = relationship("Event", back_populates="seats")
    booking = relationship("Booking", back_populates="seats")

    def __repr__(self):
        return f"<Seat {self.seat_label}>"

class Payment(Base):
    """Tabel Payments"""
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey('bookings.id'), unique=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)
    payment_date = Column(DateTime, default=func.now())
    status = Column(String(20), default='Success', nullable=False)

    booking = relationship("Booking", back_populates="payment")