from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
# from models import User, Event, Booking, Payment <-- HAPUS 
from ticket_system_core.models import User, Event, Booking, Payment # <-- GANTI 
import bcrypt 
from datetime import datetime
import random
import string

# --- KONFIGURASI APLIKASI ---
VALID_ROLES = ['Customer', 'Admin'] 
DB_URL = "postgresql://postgres:sigmoid@localhost:5433/ticket_db"

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)


# ===============================================
# [0] UTILITAS & KEAMANAN
# ===============================================

def hash_password(raw_password: str) -> str:
    return bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(raw_password: str, hashed_password: str | None) -> bool:
    if not hashed_password: return False
    return bcrypt.checkpw(raw_password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_booking_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return f"BKG-{''.join(random.choice(chars) for _ in range(5))}"

# --- HELPER INPUT (Anti-Crash) ---
def get_valid_int(prompt: str) -> int:
    while True:
        try: return int(input(prompt).strip())
        except ValueError: print("❌ Input harus ANGKA BULAT.")

def get_valid_float(prompt: str) -> float:
    while True:
        try: return float(input(prompt).strip())
        except ValueError: print("❌ Input harus ANGKA (Bisa desimal).")

def get_valid_date(prompt: str) -> str:
    while True:
        v = input(prompt).strip()
        try:
            datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            return v
        except ValueError: print("❌ Format Salah! Gunakan: YYYY-MM-DD HH:MM:SS")

def authenticate_admin() -> User | None:
    print("\n🔒 AKSES ADMIN DIPERLUKAN")
    email = input("Email Admin: ")
    pwd = input("Password: ")
    session = Session()
    try:
        user = session.query(User).filter_by(email=email).first()
        if user and user.role == 'Admin' and check_password(pwd, user.password):
            print(f"✅ Akses Diberikan. Halo {user.name}.")
            return user
        print("❌ AKSES DITOLAK.")
        return None
    finally:
        session.close()


# ===============================================
# [1] CRUD USER
# ===============================================

def add_user(name: str, email: str, raw_password: str, role: str) -> User | None:
    if role not in VALID_ROLES:
        print(f"❌ Role tidak valid. Pilih: {VALID_ROLES}")
        return None
    session = Session()
    try:
        new_user = User(name=name, email=email, role=role, password=hash_password(raw_password))
        session.add(new_user)
        session.commit()
        print(f"✅ User Registered: {name} ({role})")
        return new_user
    except IntegrityError:
        session.rollback()
        print("❌ Email sudah terdaftar.")
        return None
    finally:
        session.close()

def get_all_users() -> list[User]:
    session = Session()
    try: return session.query(User).order_by(User.id).all()
    finally: session.close()

def update_user_password(email: str, new_raw_password: str) -> bool:
    session = Session()
    try:
        user = session.query(User).filter_by(email=email).first()
        if user:
            user.password = hash_password(new_raw_password)
            session.commit()
            print("✅ Password berhasil diubah.")
            return True
        print("❌ User tidak ditemukan.")
        return False
    finally:
        session.close()

def delete_user(email: str) -> bool:
    session = Session()
    try:
        user = session.query(User).filter_by(email=email).first()
        if user:
            session.delete(user)
            session.commit()
            print(f"✅ User {email} dihapus.")
            return True
        print("❌ User tidak ditemukan.")
        return False
    except Exception as e:
        session.rollback()
        print(f"❌ Gagal Hapus: {e}")
        return False
    finally:
        session.close()


# ===============================================
# [2] CRUD EVENT
# ===============================================

def add_event(admin_user: User, name: str, description: str, date_str: str, venue: str, capacity: int, ticket_price: float) -> Event | None:
    session = Session()
    try:
        new_event = Event(
            admin_id=admin_user.id, name=name, description=description,
            date=datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S'),
            venue=venue, capacity=capacity, ticket_price=ticket_price
        )
        session.add(new_event)
        session.commit()
        print(f"✅ Event Created: '{name}'")
        return new_event
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        return None
    finally:
        session.close()

def get_all_events() -> list[Event]:
    session = Session()
    try: return session.query(Event).options(joinedload(Event.admin)).order_by(Event.date).all()
    finally: session.close()

def update_event_price(event_id: int, new_price: float) -> bool:
    session = Session()
    try:
        event = session.query(Event).filter_by(id=event_id).first()
        if event:
            event.ticket_price = new_price
            session.commit()
            print(f"✅ Harga Event ID {event_id} diupdate jadi Rp {new_price}")
            return True
        print("❌ Event tidak ditemukan.")
        return False
    finally:
        session.close()

def delete_event(event_id: int) -> bool:
    session = Session()
    try:
        event = session.query(Event).filter_by(id=event_id).first()
        if event:
            session.delete(event)
            session.commit()
            print(f"✅ Event ID {event_id} dihapus.")
            return True
        print("❌ Event tidak ditemukan.")
        return False
    except IntegrityError:
        session.rollback()
        print("❌ Gagal: Event sudah ada bookingnya. Hapus booking dulu.")
        return False
    finally:
        session.close()


# ===============================================
# [3] CRUD BOOKING
# ===============================================

def add_booking(customer_email: str, event_id: int, quantity: int) -> Booking | None:
    session = Session()
    try:
        cust = session.query(User).filter_by(email=customer_email).first()
        if not cust or cust.role != 'Customer':
            print("❌ User invalid atau bukan Customer.")
            return None

        event = session.query(Event).filter_by(id=event_id).first()
        if not event:
            print("❌ Event tidak ditemukan.")
            return None

        if event.capacity < quantity:
            print(f"❌ Kapasitas Penuh! Tersisa: {event.capacity}")
            return None

        total = event.ticket_price * quantity
        code = generate_booking_code()
        
        event.capacity -= quantity 

        new_bk = Booking(
            customer_id=cust.id, event_id=event.id,
            quantity=quantity, total_price=total, booking_code=code,
            status='Pending'
        )
        session.add(new_bk)
        session.commit()
        print(f"✅ Booking Berhasil! Kode: {code} | Total: Rp {total:,.2f}")
        print("   Status: PENDING (Segera lakukan pembayaran)")
        return new_bk
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        return None
    finally:
        session.close()

def get_all_bookings() -> list[Booking]:
    session = Session()
    try: return session.query(Booking).options(joinedload(Booking.event), joinedload(Booking.customer)).all()
    finally: session.close()

def get_my_bookings(email: str) -> list[Booking]:
    session = Session()
    try:
        user = session.query(User).filter_by(email=email).first()
        if not user: return []
        return session.query(Booking).filter_by(customer_id=user.id).options(joinedload(Booking.event)).all()
    finally:
        session.close()

def cancel_booking(booking_code: str) -> bool:
    session = Session()
    try:
        bk = session.query(Booking).filter_by(booking_code=booking_code).first()
        if not bk:
            print("❌ Booking tidak ditemukan.")
            return False
        
        if bk.status == 'Confirmed':
            print("⚠️ Booking sudah Confirmed. Hubungi Admin untuk refund.")
            return False

        event = session.query(Event).filter_by(id=bk.event_id).first()
        if event: event.capacity += bk.quantity
            
        # Ganti status jadi Cancelled (Soft Delete)
        bk.status = 'Cancelled'
        session.commit()
        print(f"✅ Booking {booking_code} status: CANCELLED. Kuota dikembalikan.")
        return True
    finally:
        session.close()


# ===============================================
# [4] CRUD PAYMENT (New & Full)
# ===============================================

def make_payment(booking_code: str, amount: float, method: str) -> bool:
    session = Session()
    try:
        bk = session.query(Booking).filter_by(booking_code=booking_code).first()
        if not bk:
            print("❌ Booking tidak ditemukan.")
            return False
        
        if bk.status != 'Pending':
            print(f"❌ Gagal Bayar: Status Booking saat ini adalah '{bk.status}'")
            return False
        
        if amount < bk.total_price:
            print(f"❌ Uang Kurang! Total: {bk.total_price}, Dibayar: {amount}")
            return False

        # Create Payment
        new_pay = Payment(
            booking_id=bk.id,
            amount=amount,
            payment_method=method,
            status='Success'
        )
        session.add(new_pay)
        
        # Update Booking Status
        bk.status = 'Confirmed'
        
        session.commit()
        print(f"✅ PEMBAYARAN SUKSES! Booking {booking_code} -> CONFIRMED.")
        return True
    except Exception as e:
        session.rollback()
        print(f"❌ Error Payment: {e}")
        return False
    finally:
        session.close()

def get_all_payments() -> list[Payment]:
    """Admin Only: Lihat semua transaksi masuk."""
    session = Session()
    try: return session.query(Payment).options(joinedload(Payment.booking)).all()
    finally: session.close()

def get_payment_detail(booking_code: str) -> Payment | None:
    session = Session()
    try:
        bk = session.query(Booking).filter_by(booking_code=booking_code).first()
        if not bk: return None
        return session.query(Payment).filter_by(booking_id=bk.id).first()
    finally:
        session.close()

def refund_payment(payment_id: int) -> bool:
    """Admin Only: Simulasi Refund & Batalkan Booking Confirmed."""
    session = Session()
    try:
        pay = session.query(Payment).filter_by(id=payment_id).first()
        if not pay:
            print("❌ Payment ID tidak ditemukan.")
            return False
        
        # Ubah status payment
        pay.status = 'Refunded'
        
        # Ubah status booking terkait
        bk = session.query(Booking).filter_by(id=pay.booking_id).first()
        if bk:
            bk.status = 'Cancelled'
            # Kembalikan kuota event
            event = session.query(Event).filter_by(id=bk.event_id).first()
            if event: event.capacity += bk.quantity

        session.commit()
        print(f"✅ REFUND BERHASIL (ID: {payment_id}). Booking dibatalkan.")
        return True
    finally:
        session.close()


# ===============================================
# MENU UTAMA (Ultimate)
# ===============================================

def main_menu():
    while True:
        print("\n" + "="*45)
        print("   TICKET SYSTEM ULTIMATE (User/Event/Book/Pay)")
        print("="*45)
        
        # --- USER ---
        print("\n[👤 USER CRUD]")
        print("1.  Create User (Register)")
        print("2.  Read All Users")
        print("3.  Update Password")
        print("4.  Delete User")

        # --- EVENT ---
        print("\n[📅 EVENT CRUD (Admin Auth)]")
        print("5.  Create Event")
        print("6.  Read All Events")
        print("7.  Update Event Price")
        print("8.  Delete Event")

        # --- BOOKING ---
        print("\n[🎫 BOOKING CRUD]")
        print("9.  Create Booking (Customer)")
        print("10. Read My Bookings (Customer)")
        print("11. Read All Bookings (Admin)")
        print("12. Update/Cancel Booking (Pending Only)")
        
        # --- PAYMENT ---
        print("\n[💰 PAYMENT CRUD]")
        print("13. Create Payment (Bayar Tiket)")
        print("14. Read Payment Detail (by Booking Code)")
        print("15. Read All Payments (Admin)")
        print("16. Delete/Refund Payment (Admin)")

        print("\n0.  EXIT")
        
        c = input("\n>> Pilih Menu (0-16): ").strip()

        # [USER]
        if c == '1':
            add_user(input("Nama: "), input("Email: "), input("Password: "), input("Role (Customer/Admin): "))
        elif c == '2':
            for u in get_all_users(): print(f"[{u.id}] {u.name} ({u.role}) | {u.email}")
        elif c == '3':
            update_user_password(input("Email: "), input("New Pass: "))
        elif c == '4':
            delete_user(input("Email to Delete: "))

        # [EVENT]
        elif c == '5':
            admin = authenticate_admin()
            if admin:
                add_event(admin, input("Name: "), input("Desc: "), get_valid_date("Date YYYY-MM-DD HH:MM:SS: "), input("Venue: "), get_valid_int("Capacity: "), get_valid_float("Price: "))
        elif c == '6':
            for e in get_all_events(): print(f"[{e.id}] {e.name} | Rp {e.ticket_price} | Sisa: {e.capacity}")
        elif c == '7':
            admin = authenticate_admin()
            if admin:
                update_event_price(get_valid_int("Event ID: "), get_valid_float("New Price: "))
        elif c == '8':
            admin = authenticate_admin()
            if admin:
                delete_event(get_valid_int("Event ID: "))

        # [BOOKING]
        elif c == '9':
            add_booking(input("Customer Email: "), get_valid_int("Event ID: "), get_valid_int("Qty: "))
        elif c == '10':
            for b in get_my_bookings(input("My Email: ")): 
                print(f"[{b.booking_code}] {b.event.name} | Status: {b.status} | Rp {b.total_price}")
        elif c == '11':
            admin = authenticate_admin()
            if admin:
                for b in get_all_bookings(): print(f"[{b.booking_code}] User: {b.customer.email} -> EventID: {b.event_id} ({b.status})")
        elif c == '12':
            cancel_booking(input("Booking Code to Cancel: "))

        # [PAYMENT]
        elif c == '13':
            print("\n--- FORM PEMBAYARAN ---")
            code = input("Kode Booking: ")
            amt = get_valid_float("Nominal Bayar: ")
            mth = input("Metode (Transfer/Cash): ")
            make_payment(code, amt, mth)
        elif c == '14':
            pay = get_payment_detail(input("Booking Code: "))
            if pay: print(f"ID: {pay.id} | Amount: {pay.amount} | Status: {pay.status} | Date: {pay.payment_date}")
            else: print("Belum ada data pembayaran.")
        elif c == '15':
            admin = authenticate_admin()
            if admin:
                for p in get_all_payments(): print(f"PayID: {p.id} -> BookID: {p.booking.booking_code} | Rp {p.amount} ({p.status})")
        elif c == '16':
            admin = authenticate_admin()
            if admin:
                refund_payment(get_valid_int("Payment ID to Refund: "))

        elif c == '0':
            print("Bye!"); break
        else:
            print("Pilihan tidak tersedia.")

if __name__ == "__main__":
    main_menu()