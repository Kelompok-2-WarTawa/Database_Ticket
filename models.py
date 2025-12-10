from sqlalchemy import Column, DateTime, String, Integer, Text, Numeric, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# Inisialisasi Base dan Metadata
Base = declarative_base()
metadata = Base.metadata # Penting untuk Alembic autogenerate

class User(Base):
    """Tabel Users: Untuk Attendee dan Organizer (Fitur 1)"""
    __tablename__ = 'users'
    
    # Kolom Dasar
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False) # 'Attendee' atau 'Organizer'
    
    # Relasi ORM
    # User (Organizer) punya banyak Events
    organized_events = relationship("Event", back_populates="organizer")
    # User (Attendee) punya banyak Bookings
    bookings = relationship("Booking", back_populates="attendee")

    def __repr__(self):
        return f"<User id={self.id}, email={self.email}, role={self.role}>"


class Event(Base):
    """Tabel Events: Data Event yang dibuat oleh Organizer (Fitur 2)"""
    __tablename__ = 'events'
    
    # Kolom Dasar
    id = Column(Integer, primary_key=True)
    organizer_id = Column(Integer, ForeignKey('users.id'), nullable=False) # FK ke User
    name = Column(String(255), nullable=False)
    description = Column(Text)
    date = Column(DateTime, nullable=False)
    venue = Column(String(255), nullable=False)
    capacity = Column(Integer, nullable=False)
    ticket_price = Column(Numeric(10, 2), nullable=False)
    
    # Relasi ORM
    # Event dimiliki oleh satu User (Organizer)
    organizer = relationship("User", back_populates="organized_events")
    # Event punya banyak Bookings
    bookings = relationship("Booking", back_populates="event")

    def __repr__(self):
        return f"<Event id={self.id}, name={self.name}, date={self.date}>"


class Booking(Base):
    """Tabel Bookings: Data Pemesanan Tiket (Fitur 3, 4, 5)"""
    __tablename__ = 'bookings'
    
    # Kolom Dasar
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False) # FK ke Event
    attendee_id = Column(Integer, ForeignKey('users.id'), nullable=False) # FK ke User
    quantity = Column(Integer, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    booking_code = Column(String(50), unique=True, nullable=False) # Untuk konfirmasi tiket
    booking_date = Column(DateTime, default=func.now())
    
    # Relasi ORM
    # Booking terkait ke satu Event
    event = relationship("Event", back_populates="bookings")
    # Booking terkait ke satu User (Attendee)
    attendee = relationship("User", back_populates="bookings")

    def __repr__(self):
        return f"<Booking id={self.id}, code={self.booking_code}, quantity={self.quantity}>"