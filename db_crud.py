from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from models import User, Event, Booking 
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
# FUNGSI UTILITAS & KEAMANAN
# ===============================================

def hash_password(raw_password: str) -> str:
    return bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(raw_password: str, hashed_password: str | None) -> bool:
    if not hashed_password: return False
    return bcrypt.checkpw(raw_password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_booking_code() -> str:
    """Membuat kode unik: BKG-9X2A1"""
    chars = string.ascii_uppercase + string.digits
    random_str = ''.join(random.choice(chars) for _ in range(5))
    return f"BKG-{random_str}"


# ===============================================
# [1] CRUD USER (Expanded)
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
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        session.close()

def get_all_users() -> list[User]:
    session = Session()
    try:
        return session.query(User).order_by(User.id).all()
    finally:
        session.close()

def get_user_by_email(email: str) -> User | None:
    session = Session()
    try:
        return session.query(User).filter_by(email=email).first()
    finally:
        session.close()

def update_user_profile(email: str, new_name: str) -> bool:
    session = Session()
    try:
        user = session.query(User).filter_by(email=email).first()
        if user:
            user.name = new_name
            session.commit()
            print(f"✅ Nama user diperbarui menjadi: {new_name}")
            return True
        print("❌ User tidak ditemukan.")
        return False
    finally:
        session.close()

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
    finally:
        session.close()

def login_user(email: str, raw_password: str) -> bool:
    user = get_user_by_email(email)
    if user and check_password(raw_password, user.password):
        print(f"✅ LOGIN SUKSES! Halo {user.name} ({user.role})")
        return True
    print("❌ Login Gagal: Email atau Password salah.")
    return False


# ===============================================
# [2] CRUD EVENT (Expanded)
# ===============================================

def add_event(admin_email: str, name: str, description: str, date_str: str, venue: str, capacity: int, ticket_price: float) -> Event | None:
    session = Session()
    try:
        admin = session.query(User).filter_by(email=admin_email).first()
        if not admin or admin.role != 'Admin':
            print("❌ Akses Ditolak: Hanya Admin yang bisa membuat event.")
            return None

        event_dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        new_event = Event(
            admin_id=admin.id, name=name, description=description,
            date=event_dt, venue=venue, capacity=capacity, ticket_price=ticket_price
        )
        session.add(new_event)
        session.commit()
        print(f"✅ Event Created: '{name}'")
        return new_event
    except ValueError:
        print("❌ Format tanggal salah (YYYY-MM-DD HH:MM:SS)")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        session.close()

def get_all_events() -> list[Event]:
    session = Session()
    try:
        return session.query(Event).options(joinedload(Event.admin)).order_by(Event.date).all()
    finally:
        session.close()

def search_events(keyword: str) -> list[Event]:
    """Mencari event berdasarkan Nama atau Venue (Case Insensitive)."""
    session = Session()
    try:
        search = f"%{keyword}%"
        return session.query(Event).filter(
            or_(Event.name.ilike(search), Event.venue.ilike(search))
        ).options(joinedload(Event.admin)).all()
    finally:
        session.close()

def get_events_by_admin(admin_email: str) -> list[Event]:
    session = Session()
    try:
        admin = session.query(User).filter_by(email=admin_email).first()
        if not admin: return []
        return session.query(Event).filter_by(admin_id=admin.id).all()
    finally:
        session.close()

def update_event_details(event_id: int, new_venue: str = None, new_date_str: str = None) -> bool:
    session = Session()
    try:
        event = session.query(Event).filter_by(id=event_id).first()
        if not event:
            print("❌ Event tidak ditemukan.")
            return False
        
        if new_venue: event.venue = new_venue
        if new_date_str: event.date = datetime.strptime(new_date_str, '%Y-%m-%d %H:%M:%S')
        
        session.commit()
        print(f"✅ Event ID {event_id} diperbarui.")
        return True
    except ValueError:
        print("❌ Format tanggal salah.")
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
    except Exception as e: # Handle FK constraint (hapus booking dulu)
        session.rollback()
        print(f"❌ Gagal Hapus: Event mungkin memiliki booking aktif. Hapus booking terlebih dahulu.")
        return False
    finally:
        session.close()


# ===============================================
# [3] CRUD BOOKING (Expanded)
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

        # Logic Booking
        total = event.ticket_price * quantity
        code = generate_booking_code()
        event.capacity -= quantity # Kurangi kapasitas

        new_bk = Booking(
            customer_id=cust.id, event_id=event.id,
            quantity=quantity, total_price=total, booking_code=code
        )
        session.add(new_bk)
        session.commit()
        print(f"✅ Booking Sukses! Code: {code} | Total: Rp {total:,.2f}")
        return new_bk
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        return None
    finally:
        session.close()

def get_all_bookings() -> list[Booking]:
    session = Session()
    try:
        return session.query(Booking).options(joinedload(Booking.event), joinedload(Booking.customer)).all()
    finally:
        session.close()

def get_bookings_by_customer(email: str) -> list[Booking]:
    session = Session()
    try:
        user = session.query(User).filter_by(email=email).first()
        if not user: return []
        return session.query(Booking).filter_by(customer_id=user.id).options(joinedload(Booking.event)).all()
    finally:
        session.close()

def get_booking_by_code(code: str) -> Booking | None:
    session = Session()
    try:
        return session.query(Booking).filter_by(booking_code=code).options(joinedload(Booking.event), joinedload(Booking.customer)).first()
    finally:
        session.close()

def cancel_booking(booking_code: str) -> bool:
    session = Session()
    try:
        bk = session.query(Booking).filter_by(booking_code=booking_code).first()
        if not bk:
            print("❌ Booking tidak ditemukan.")
            return False
        
        # Kembalikan kapasitas
        event = session.query(Event).filter_by(id=bk.event_id).first()
        if event: event.capacity += bk.quantity
            
        session.delete(bk)
        session.commit()
        print(f"✅ Booking {booking_code} dibatalkan. Dana dikembalikan (Simulasi).")
        return True
    finally:
        session.close()


# ===============================================
# MENU UTAMA (Grouped)
# ===============================================

def main_menu():
    while True:
        print("\n" + "="*40)
        print("   TICKET SYSTEM SUPER APP (Admin/Cust)")
        print("="*40)
        
        print("\n[👤 USER MANAGEMENT]")
        print("1.  Register User")
        print("2.  List All Users")
        print("3.  Find User by Email")
        print("4.  Update User Profile (Name)")
        print("5.  Change Password")
        print("6.  Delete User")
        print("7.  Login Simulation")

        print("\n[📅 EVENT MANAGEMENT]")
        print("8.  Create Event (Admin Only)")
        print("9.  List All Events")
        print("10. Search Events (by Name/Venue)")
        print("11. List Events by Admin")
        print("12. Update Event Details (Date/Venue)")
        print("13. Update Event Price") # Opsional, bisa digabung tapi dipisah biar banyak fitur
        print("14. Delete Event")

        print("\n[🎫 BOOKING SYSTEM]")
        print("15. Book Ticket (Customer Only)")
        print("16. List All Bookings (Admin View)")
        print("17. My Bookings (Customer History)")
        print("18. Check Booking Status (by Code)")
        print("19. Cancel Booking")
        
        print("\n0.  EXIT")
        
        c = input("\n>> Pilih Menu (0-19): ").strip()

        # --- USER ---
        if c == '1':
            add_user(input("Nama: "), input("Email: "), input("Password: "), input("Role (Customer/Admin): "))
        elif c == '2':
            for u in get_all_users(): print(f"[{u.id}] {u.name} | {u.email} | {u.role}")
        elif c == '3':
            u = get_user_by_email(input("Email: "))
            print(f"Found: {u.name} ({u.role})" if u else "Not Found")
        elif c == '4':
            update_user_profile(input("Email: "), input("New Name: "))
        elif c == '5':
            update_user_password(input("Email: "), input("New Password: "))
        elif c == '6':
            delete_user(input("Email to Delete: "))
        elif c == '7':
            login_user(input("Email: "), input("Password: "))

        # --- EVENT ---
        elif c == '8':
            add_event(input("Admin Email: "), input("Event Name: "), input("Desc: "), input("Date (YYYY-MM-DD HH:MM:SS): "), input("Venue: "), int(input("Capacity: ")), float(input("Price: ")))
        elif c == '9':
            for e in get_all_events(): print(f"[{e.id}] {e.date} | {e.name} @ {e.venue} | Rp {e.ticket_price} | By: {e.admin.name if e.admin else '?'}")
        elif c == '10':
            res = search_events(input("Keyword (Name/Venue): "))
            for e in res: print(f"- {e.name} di {e.venue}")
        elif c == '11':
            res = get_events_by_admin(input("Admin Email: "))
            for e in res: print(f"- {e.name} ({e.date})")
        elif c == '12':
            eid = int(input("Event ID: "))
            v = input("New Venue (kosongkan jika tetap): ")
            d = input("New Date YYYY-MM-DD HH:MM:SS (kosongkan jika tetap): ")
            update_event_details(eid, v if v else None, d if d else None)
        elif c == '13':
             # Fitur update price sederhana, bisa diimplementasikan ulang di fungsi update_event_details jika mau
             # Tapi di sini saya anggap user ingin update terpisah
             print("Gunakan opsi 12 untuk update detail, atau buat fungsi khusus update price jika perlu.") 
        elif c == '14':
            delete_event(int(input("Event ID to Delete: ")))

        # --- BOOKING ---
        elif c == '15':
            add_booking(input("Customer Email: "), int(input("Event ID: ")), int(input("Qty: ")))
        elif c == '16':
            for b in get_all_bookings(): print(f"[{b.booking_code}] {b.customer.email} -> {b.event.name} ({b.quantity} pcs)")
        elif c == '17':
            res = get_bookings_by_customer(input("Customer Email: "))
            for b in res: print(f"- {b.booking_code}: {b.event.name} | Total: {b.total_price}")
        elif c == '18':
            b = get_booking_by_code(input("Booking Code: "))
            if b: print(f"VALID: {b.customer.name} going to {b.event.name} on {b.event.date}")
            else: print("INVALID CODE")
        elif c == '19':
            cancel_booking(input("Booking Code to Cancel: "))

        elif c == '0':
            print("Bye!"); break
        else:
            print("Pilihan tidak tersedia.")

if __name__ == "__main__":
    main_menu()