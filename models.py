from sqlalchemy import Column, DateTime, String, Integer, Text, Numeric, ForeignKey, func, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# Inisialisasi Base dan Metadata
Base = declarative_base()
metadata = Base.metadata

class User(Base):
    """
    Tabel Users:
    - Admin: Pengelola yang membuat Event.
    - Customer: Pengguna yang membeli tiket (Booking).
    """
    __tablename__ = 'users'
    
    # CONSTRAINT: Role hanya boleh 'Customer' atau 'Admin'
    __table_args__ = (
        CheckConstraint(
            "role IN ('Customer', 'Admin')", 
            name='check_user_role'
        ),
    )
    
    # Kolom Dasar
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False) # 'Customer' atau 'Admin'
    
    # Relasi ORM
    # Jika user adalah Admin, dia punya banyak event yang dikelola
    admin_events = relationship("Event", back_populates="admin")
    
    # Jika user adalah Customer, dia punya banyak booking
    bookings = relationship("Booking", back_populates="customer")

    def __repr__(self):
        return f"<User id={self.id}, email={self.email}, role={self.role}>"


class Event(Base):
    """Tabel Events: Data Event yang dibuat oleh Admin"""
    __tablename__ = 'events'
    
    # Kolom Dasar
    id = Column(Integer, primary_key=True)
    
    # GANTI: organizer_id -> admin_id
    admin_id = Column(Integer, ForeignKey('users.id'), nullable=False) 
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    date = Column(DateTime, nullable=False)
    venue = Column(String(255), nullable=False)
    capacity = Column(Integer, nullable=False)
    ticket_price = Column(Numeric(10, 2), nullable=False)
    
    # Relasi ORM
    # Event dimiliki oleh satu User (Admin)
    admin = relationship("User", back_populates="admin_events")
    
    # Event punya banyak Bookings
    bookings = relationship("Booking", back_populates="event")

    def __repr__(self):
        return f"<Event id={self.id}, name={self.name}, date={self.date}>"


class Booking(Base):
    """Tabel Bookings: Data Pemesanan Tiket oleh Customer"""
    __tablename__ = 'bookings'
    
    # Kolom Dasar
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    
    # GANTI: attendee_id -> customer_id
    customer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    booking_code = Column(String(50), unique=True, nullable=False)
    booking_date = Column(DateTime, default=func.now())
    
    # Relasi ORM
    # Booking terkait ke satu Event
    event = relationship("Event", back_populates="bookings")
    
    # Booking dimiliki oleh satu User (Customer)
    customer = relationship("User", back_populates="bookings")

    def __repr__(self):
        return f"<Booking id={self.id}, code={self.booking_code}, quantity={self.quantity}>"