from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy.exc import IntegrityError
from models import User, Event, Booking, Payment, Seat
import bcrypt 
from datetime import datetime
import random
import string

# --- KONFIGURASI ---
VALID_ROLES = ['Customer', 'Admin'] 
DB_URL = "postgresql://postgres:sigmoid@localhost:5433/ticket_db"

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

# ===============================================
# [0] UTILITAS & AUTH
# ===============================================
def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(raw: str, hashed: str | None) -> bool:
    if not hashed: return False
    return bcrypt.checkpw(raw.encode('utf-8'), hashed.encode('utf-8'))

def generate_booking_code() -> str:
    return f"BKG-{ ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)) }"

def get_input(prompt, type_func=str):
    while True:
        try: return type_func(input(prompt).strip())
        except ValueError: print(f"❌ Input salah. Harap masukkan {type_func.__name__}.")

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
        print("❌ Login Gagal / Bukan Admin.")
        return None
    finally:
        session.close()

# ===============================================
# [1] CRUD USER (LENGKAP)
# ===============================================
def register_user(name, email, pwd, role, phone):
    session = Session()
    try:
        if role not in VALID_ROLES: raise ValueError("Role tidak valid")
        u = User(name=name, email=email, role=role, password=hash_password(pwd), phone_number=phone)
        session.add(u)
        session.commit()
        print(f"✅ User {name} (Telp: {phone}) berhasil didaftarkan!")
    except IntegrityError:
        session.rollback(); print("❌ Email sudah terdaftar.")
    except Exception as e:
        session.rollback(); print(f"❌ Error: {e}")
    finally: session.close()

def list_users():
    session = Session()
    print("\n--- DAFTAR PENGGUNA ---")
    for u in session.query(User).order_by(User.id).all(): 
        print(f"[{u.id}] {u.name} ({u.role}) | 📞 {u.phone_number or '-'} | ✉️ {u.email}")
    session.close()

def update_user_password(email, new_pass):
    session = Session()
    user = session.query(User).filter_by(email=email).first()
    if user:
        user.password = hash_password(new_pass)
        session.commit()
        print("✅ Password berhasil diubah.")
    else: print("❌ User tidak ditemukan.")
    session.close()

def delete_user(email):
    session = Session()
    try:
        user = session.query(User).filter_by(email=email).first()
        if user:
            session.delete(user)
            session.commit()
            print(f"✅ User {email} dihapus.")
        else: print("❌ User tidak ditemukan.")
    except Exception as e:
        session.rollback(); print(f"❌ Gagal hapus (Mungkin ada data terkait): {e}")
    finally: session.close()

# ===============================================
# [2] CRUD EVENT & SEAT (LENGKAP)
# ===============================================
def create_event(admin_user):
    print("\n--- BUAT EVENT BARU ---")
    name = get_input("Nama Event: ")
    desc = get_input("Deskripsi: ")
    date_str = get_input("Tanggal (YYYY-MM-DD HH:MM:SS): ")
    venue = get_input("Lokasi: ")
    capacity = get_input("Total Kapasitas: ", int)
    price = get_input("Harga Tiket: ", float)
    
    session = Session()
    try:
        event = Event(
            admin_id=admin_user.id, name=name, description=desc,
            date=datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S'),
            venue=venue, total_capacity=capacity, ticket_price=price
        )
        session.add(event)
        session.commit()
        print(f"✅ Event '{name}' dibuat! ID: {event.id}")
        
        if input("Generate kursi otomatis? (y/n): ").lower() == 'y':
            generate_seats(event.id, capacity)
    except Exception as e: print(f"❌ Error: {e}")
    finally: session.close()

def generate_seats(event_id, qty):
    session = Session()
    try:
        event = session.query(Event).get(event_id)
        if not event: return print("Event tidak ditemukan")

        print("⏳ Sedang men-generate kursi...")
        # Cek kursi terakhir untuk melanjutkan nomor
        last_seat = session.query(Seat).filter_by(event_id=event_id).order_by(Seat.id.desc()).first()
        start_num = 1
        if last_seat:
            # Simple logic: kalau S005, ambil 5.
            try: start_num = int(last_seat.seat_label[1:]) + 1
            except: pass

        seats = []
        for i in range(qty):
            label = f"S{start_num + i:03d}" 
            seats.append(Seat(event_id=event.id, seat_label=label, is_booked=False))
        
        session.add_all(seats)
        session.commit()
        print(f"✅ Berhasil menambah {qty} kursi ke Event '{event.name}'!")
    except Exception as e: print(f"❌ Gagal: {e}")
    finally: session.close()

def list_events():
    session = Session()
    print("\n--- DAFTAR EVENT ---")
    for e in session.query(Event).order_by(Event.date).all():
        total = session.query(Seat).filter_by(event_id=e.id).count()
        booked = session.query(Seat).filter_by(event_id=e.id, is_booked=True).count()
        print(f"🎫 [{e.id}] {e.name} | {e.date}")
        print(f"   💰 Rp {e.ticket_price:,.0f} | 💺 Kursi: {total-booked} / {total}")
    session.close()

def update_event_price(event_id, new_price):
    session = Session()
    e = session.query(Event).get(event_id)
    if e:
        e.ticket_price = new_price
        session.commit()
        print("✅ Harga diupdate.")
    else: print("❌ Event tidak ditemukan.")
    session.close()

def delete_event(event_id):
    session = Session()
    try:
        e = session.query(Event).get(event_id)
        if e:
            session.delete(e)
            session.commit()
            print("✅ Event dihapus.")
        else: print("❌ Event tidak ditemukan.")
    except Exception as e: session.rollback(); print(f"❌ Gagal: {e}")
    finally: session.close()

def view_seat_map(event_id):
    session = Session()
    seats = session.query(Seat).filter_by(event_id=event_id).order_by(Seat.seat_label).all()
    if not seats: return print("❌ Tidak ada data kursi.")

    print(f"\n--- PETA KURSI (Event ID: {event_id}) ---")
    line = ""
    for i, s in enumerate(seats):
        status = "[X]" if s.is_booked else "[O]"
        line += f"{s.seat_label}{status}  "
        if (i + 1) % 5 == 0: 
            print(line); line = ""
    print(line)
    session.close()

# ===============================================
# [3] BOOKING (LENGKAP)
# ===============================================
def create_booking_with_seats():
    email = get_input("Email Customer: ")
    event_id = get_input("ID Event: ", int)
    qty = get_input("Jumlah Tiket: ", int)
    
    session = Session()
    try:
        user = session.query(User).filter_by(email=email).first()
        event = session.query(Event).get(event_id)
        
        if not user or not event: return print("❌ User/Event invalid.")
        
        # Lock & Ambil Kursi
        available_seats = session.query(Seat).filter_by(event_id=event.id, is_booked=False).limit(qty).with_for_update().all()
        if len(available_seats) < qty: return print(f"❌ Kursi kurang! Sisa: {len(available_seats)}")

        total = event.ticket_price * qty
        code = generate_booking_code()
        
        # Buat Booking
        new_bk = Booking(customer_id=user.id, event_id=event.id, quantity=qty, total_price=total, booking_code=code, status='Pending')
        session.add(new_bk)
        session.flush()

        # Update Kursi
        seat_lbls = []
        for s in available_seats:
            s.is_booked = True; s.booking_id = new_bk.id
            seat_lbls.append(s.seat_label)
        
        session.commit()
        print(f"\n✅ BOOKING SUKSES! Kode: {code}")
        print(f"   Kursi: {', '.join(seat_lbls)} | Total: Rp {total:,.0f}")
    except Exception as e: session.rollback(); print(f"❌ Error: {e}")
    finally: session.close()

def my_bookings(email):
    session = Session()
    user = session.query(User).filter_by(email=email).first()
    if not user: return print("User not found.")
    
    print(f"\n--- BOOKING SAYA ({user.name}) ---")
    for b in session.query(Booking).filter_by(customer_id=user.id).options(joinedload(Booking.seats)).all():
        seats = ", ".join([s.seat_label for s in b.seats])
        print(f"🧾 {b.booking_code} | {b.status} | Kursi: {seats} | Rp {b.total_price:,.0f}")
    session.close()

def get_all_bookings():
    session = Session()
    print("\n--- SEMUA BOOKING (ADMIN) ---")
    for b in session.query(Booking).all():
        print(f"{b.booking_code} | User: {b.customer_id} | Event: {b.event_id} | {b.status}")
    session.close()

def cancel_booking(code):
    session = Session()
    try:
        bk = session.query(Booking).filter_by(booking_code=code).first()
        if not bk or bk.status != 'Pending': return print("❌ Tidak bisa cancel.")

        # Lepas Kursi
        for s in session.query(Seat).filter_by(booking_id=bk.id).all():
            s.is_booked = False; s.booking_id = None
        
        bk.status = 'Cancelled'
        session.commit()
        print(f"✅ Booking {code} DIBATALKAN.")
    except Exception as e: session.rollback(); print(f"Error: {e}")
    finally: session.close()

# ===============================================
# [4] PAYMENT (LENGKAP)
# ===============================================
def process_payment():
    code = get_input("Kode Booking: ")
    amt = get_input("Nominal: ", float)
    method = get_input("Metode: ")
    
    session = Session()
    try:
        bk = session.query(Booking).filter_by(booking_code=code).first()
        if not bk or bk.status != 'Pending': return print("❌ Invalid booking.")
        if amt < bk.total_price: return print("❌ Uang kurang.")

        pay = Payment(booking_id=bk.id, amount=amt, payment_method=method, status='Success')
        session.add(pay)
        bk.status = 'Confirmed'
        session.commit()
        print("✅ PEMBAYARAN BERHASIL!")
    except Exception as e: session.rollback(); print(f"Error: {e}")
    finally: session.close()

def get_payment_detail(code):
    session = Session()
    bk = session.query(Booking).filter_by(booking_code=code).first()
    if bk and bk.payment:
        p = bk.payment
        print(f"💰 ID: {p.id} | Tgl: {p.payment_date} | Rp {p.amount:,.0f} | Via: {p.payment_method}")
    else: print("❌ Data pembayaran tidak ditemukan.")
    session.close()

def get_all_payments():
    session = Session()
    print("\n--- DATA KEUANGAN ---")
    for p in session.query(Payment).all():
        print(f"ID:{p.id} | Booking:{p.booking_id} | +Rp {p.amount:,.0f}")
    session.close()

def refund_payment(pay_id):
    session = Session()
    try:
        pay = session.query(Payment).get(pay_id)
        if not pay: return print("Payment not found.")
        
        pay.status = 'Refunded'
        bk = session.query(Booking).get(pay.booking_id)
        if bk:
            bk.status = 'Cancelled'
            # Lepas kursi
            for s in session.query(Seat).filter_by(booking_id=bk.id).all():
                s.is_booked = False; s.booking_id = None
        
        session.commit()
        print(f"✅ Refund ID {pay_id} Berhasil. Booking dibatalkan & Kursi dikosongkan.")
    except Exception as e: session.rollback(); print(f"Error: {e}")
    finally: session.close()

# ===============================================
# MAIN MENU (ULTIMATE 20)
# ===============================================
def main_menu():
    while True:
        print("\n" + "="*50)
        print("   🎟️  SISTEM TIKET ULTIMATE (SEAT + PHONE)  🎟️")
        print("="*50)
        
        print("[USER]")
        print("1. Register User Baru (+No HP)")
        print("2. Lihat Semua User")
        print("3. Update Password")
        print("4. Hapus User")

        print("\n[EVENT - ADMIN]")
        print("5. Buat Event (+Auto Seats)")
        print("6. Lihat Daftar Event & Kuota")
        print("7. Update Harga Event")
        print("8. Hapus Event")
        print("9. Generate Kursi Tambahan")
        print("10. Lihat Peta Kursi (Map)")

        print("\n[BOOKING]")
        print("11. Booking Tiket (Pilih Kursi)")
        print("12. Cek Booking Saya")
        print("13. Lihat Semua Booking (Admin)")
        print("14. Cancel Booking (Pending)")

        print("\n[PAYMENT]")
        print("15. Bayar Booking")
        print("16. Cek Detail Pembayaran")
        print("17. Laporan Keuangan (Admin)")
        print("18. Refund Payment (Admin)")
        
        print("\n0. EXIT")

        p = get_input("\n>> Pilih Menu: ")

        if p == '1': register_user(get_input("Nama: "), get_input("Email: "), get_input("Pass: "), get_input("Role: "), get_input("Telp: "))
        elif p == '2': list_users()
        elif p == '3': update_user_password(get_input("Email: "), get_input("New Pass: "))
        elif p == '4': delete_user(get_input("Email Hapus: "))
        
        elif p == '5': 
            adm = authenticate_admin()
            if adm: create_event(adm)
        elif p == '6': list_events()
        elif p == '7': 
            adm = authenticate_admin()
            if adm: update_event_price(get_input("Event ID: ", int), get_input("Harga Baru: ", float))
        elif p == '8': 
            adm = authenticate_admin()
            if adm: delete_event(get_input("Event ID: ", int))
        elif p == '9': 
            adm = authenticate_admin()
            if adm: generate_seats(get_input("Event ID: ", int), get_input("Jml Tambahan: ", int))
        elif p == '10': view_seat_map(get_input("Event ID: ", int))

        elif p == '11': create_booking_with_seats()
        elif p == '12': my_bookings(get_input("Email Anda: "))
        elif p == '13': 
            adm = authenticate_admin()
            if adm: get_all_bookings()
        elif p == '14': cancel_booking(get_input("Kode Booking: "))

        elif p == '15': process_payment()
        elif p == '16': get_payment_detail(get_input("Kode Booking: "))
        elif p == '17': 
            adm = authenticate_admin()
            if adm: get_all_payments()
        elif p == '18': 
            adm = authenticate_admin()
            if adm: refund_payment(get_input("Payment ID: ", int))

        elif p == '0': break
        else: print("❌ Pilihan tidak valid.")

if __name__ == "__main__":
    main_menu()