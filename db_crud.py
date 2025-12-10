from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, InternalError
from models import User, Event, Booking 
import bcrypt # Import library Bcrypt

# --- KONFIGURASI APLIKASI ---
# Daftar role yang valid
VALID_ROLES = ['Attendee', 'Organizer'] 

# URL koneksi (PostgreSQL di Docker port 5433)
DB_URL = "postgresql://postgres:sigmoid@localhost:5433/ticket_db"

# Inisialisasi Engine dan Session Factory
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)


# ===============================================
# FUNGSI KEAMANAN (Bcrypt + Salt)
# ===============================================

def hash_password(raw_password: str) -> str:
    """Menghash kata sandi mentah menggunakan Bcrypt (salt otomatis)."""
    password_bytes = raw_password.encode('utf-8')
    # gensalt() membuat salt baru
    hashed_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed_bytes.decode('utf-8')

def check_password(raw_password: str, hashed_password: str | None) -> bool: # <-- Terima string/None
    """Memverifikasi password mentah terhadap hash yang tersimpan."""
    if not hashed_password:
        return False # Jika hash yang tersimpan null, otomatis gagal
        
    raw_password_bytes = raw_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    
    return bcrypt.checkpw(raw_password_bytes, hashed_password_bytes)

# ===============================================
# FUNGING CRUD USER
# ===============================================

def add_user(name: str, email: str, raw_password: str, role: str) -> User | None:
    """Menambahkan user baru ke tabel users dengan validasi role dan hashing."""
    
    if role not in VALID_ROLES:
        print(f"❌ ERROR VALIDASI: Role '{role}' tidak valid. Role harus salah satu dari {VALID_ROLES}.")
        return None
        
    session = Session()
    try:
        # HASH PASSWORD SEBELUM DISIMPAN
        hashed_password = hash_password(raw_password)
        
        new_user = User(
            name=name,
            email=email,
            password=hashed_password, 
            role=role 
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        print(f"✅ User berhasil ditambahkan. ID: {new_user.id}, Role: {new_user.role}")
        return new_user

    except IntegrityError:
        session.rollback()
        print("❌ ERROR DATABASE: Email yang dimasukkan sudah terdaftar.")
        return None
    
    except InternalError as e:
        session.rollback()
        print("❌ ERROR DATABASE (CHECK CONSTRAINT): Role yang dimasukkan melanggar batasan database.")
        return None
        
    except Exception as e:
        session.rollback()
        print(f"❌ ERROR UMUM: {e}")
        return None
        
    finally:
        session.close()


def get_all_users() -> list[User]:
    """Mengambil semua data user."""
    session = Session()
    try:
        users = session.query(User).all()
        return users
    finally:
        session.close()

def get_user_by_email(email: str) -> User | None:
    """Mencari user berdasarkan email."""
    session = Session()
    try:
        user = session.query(User).filter_by(email=email).first()
        return user
    finally:
        session.close()

def update_user_role(email: str, new_role: str) -> bool:
    """Memperbarui role user berdasarkan email."""
    
    if new_role not in VALID_ROLES:
        print(f"❌ ERROR VALIDASI: Role '{new_role}' tidak valid. Role harus salah satu dari {VALID_ROLES}.")
        return False
        
    session = Session()
    try:
        user = session.query(User).filter_by(email=email).first()
        if user:
            user.role = new_role
            session.commit()
            print(f"✅ Role user {email} berhasil diperbarui menjadi {new_role}.")
            return True
        else:
            print(f"❌ User dengan email {email} tidak ditemukan.")
            return False
    except Exception as e:
        session.rollback()
        print(f"❌ ERROR UPDATE USER: {e}")
        return False
    finally:
        session.close()

def delete_user(email: str) -> bool:
    """Menghapus user berdasarkan email."""
    session = Session()
    try:
        user = session.query(User).filter_by(email=email).first()
        if user:
            session.delete(user)
            session.commit()
            print(f"✅ User dengan email {email} berhasil dihapus.")
            return True
        else:
            print(f"❌ User dengan email {email} tidak ditemukan.")
            return False
    except Exception as e:
        session.rollback()
        print(f"❌ ERROR DELETE USER: {e}")
        return False
    finally:
        session.close()

def login_user(email: str, raw_password: str) -> bool:
    """Mencoba login dan memverifikasi password."""
    user = get_user_by_email(email)
    
    if not user:
        print("❌ Login Gagal: Email tidak terdaftar.")
        return False
    
    # Memanggil fungsi check_password Bcrypt
    if check_password(raw_password, user.password):
        print(f"✅ Login Berhasil! Selamat datang, {user.name} ({user.role}).")
        return True
    else:
        print("❌ Login Gagal: Password salah.")
        return False


# ===============================================
# SIMULASI INTERAKSI DINAMIS (MENU UTAMA)
# ===============================================

def main_menu():
    """Menampilkan menu dan menangani input pengguna."""
    while True:
        print("\n=== OPERASI CRUD USER (Bcrypt Secured) ===")
        print("1. Tambah User (CREATE)")
        print("2. Tampilkan Semua User (READ)")
        print("3. Cari User Berdasarkan Email (READ)")
        print("4. Update Role User (UPDATE)")
        print("5. Hapus User (DELETE)")
        print("6. Tes Login User (SECURITY CHECK)")
        print("0. Keluar")
        
        choice = input("Pilih Opsi (0-6): ").strip()

        if choice == '1': # CREATE
            print("\n--- [CREATE USER] ---")
            name = input("Nama: ")
            email = input("Email: ")
            raw_password = input("Password (Raw): ")
            role = input(f"Role ({'/'.join(VALID_ROLES)}): ").strip()
            add_user(name, email, raw_password, role)

        elif choice == '2': # READ ALL
            print("\n--- [ALL USERS] ---")
            users = get_all_users()
            if users:
                for user in users:
                    print(f"ID: {user.id}, Nama: {user.name}, Email: {user.email}, Role: {user.role}, Pass(Hash): {user.password[:10]}...") 
            else:
                print("Tabel users kosong.")
        
        elif choice == '3': # READ BY EMAIL
            print("\n--- [READ USER BY EMAIL] ---")
            email = input("Masukkan Email yang dicari: ")
            user = get_user_by_email(email)
            if user:
                print(f"Ditemukan: ID={user.id}, Nama={user.name}, Role={user.role}")
            else:
                print("User tidak ditemukan.")

        elif choice == '4': # UPDATE ROLE
            print("\n--- [UPDATE ROLE] ---")
            email = input("Email User yang diupdate: ")
            new_role = input(f"Role Baru ({'/'.join(VALID_ROLES)}): ")
            update_user_role(email, new_role)

        elif choice == '5': # DELETE
            print("\n--- [DELETE USER] ---")
            email = input("Email User yang akan dihapus: ")
            delete_user(email)
            
        elif choice == '6': # TEST LOGIN
            print("\n--- [TES LOGIN] ---")
            email = input("Email Login: ")
            password = input("Password: ")
            login_user(email, password)

        elif choice == '0':
            print("Keluar dari skrip CRUD.")
            break
        else:
            print("Pilihan tidak valid. Silakan coba lagi.")


if __name__ == "__main__":
    main_menu()