from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Event, Booking # Mengimpor semua model

# --- KONFIGURASI KONEKSI ---
# Menggunakan URL koneksi yang sudah dikonfirmasi (PostgreSQL di Docker port 5433)
DB_URL = "postgresql://postgres:sigmoid@localhost:5433/ticket_db"

# Inisialisasi Engine
engine = create_engine(DB_URL)

# Buat Session Factory
Session = sessionmaker(bind=engine)


# ===============================================
# FUNGSI CRUD USER
# ===============================================

def add_user(name: str, email: str, password: str, role: str) -> User | None:
    """Menambahkan user baru ke tabel users."""
    session = Session()
    try:
        # Catatan: Dalam aplikasi nyata, password harus di-hash di sini (misalnya dengan bcrypt)
        new_user = User(
            name=name,
            email=email,
            password=password, 
            role=role
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        print(f"✅ User berhasil ditambahkan. ID: {new_user.id}, Role: {new_user.role}")
        return new_user
    except Exception as e:
        session.rollback()
        print(f"❌ ERROR CREATE USER: {e}")
        # Cek UniqueConstraint Error (misalnya email sudah ada)
        if "duplicate key value violates unique constraint" in str(e):
             print("Detail: Email yang dimasukkan sudah terdaftar.")
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


# ===============================================
# SIMULASI INTERAKSI DINAMIS
# ===============================================

def main_menu():
    """Menampilkan menu dan menangani input pengguna."""
    while True:
        print("\n=== OPERASI CRUD USER ===")
        print("1. Tambah User (CREATE)")
        print("2. Tampilkan Semua User (READ)")
        print("3. Cari User Berdasarkan Email (READ)")
        print("4. Update Role User (UPDATE)")
        print("5. Hapus User (DELETE)")
        print("0. Keluar")
        
        choice = input("Pilih Opsi (0-5): ").strip()

        if choice == '1':
            print("\n--- [CREATE USER] ---")
            name = input("Nama: ")
            email = input("Email: ")
            password = input("Password (Raw): ")
            role = input("Role (Attendee/Organizer): ")
            add_user(name, email, password, role)

        elif choice == '2':
            print("\n--- [ALL USERS] ---")
            users = get_all_users()
            if users:
                for user in users:
                    print(f"ID: {user.id}, Nama: {user.name}, Email: {user.email}, Role: {user.role}")
            else:
                print("Tabel users kosong.")
        
        elif choice == '3':
            print("\n--- [READ USER BY EMAIL] ---")
            email = input("Masukkan Email yang dicari: ")
            user = get_user_by_email(email)
            if user:
                print(f"Ditemukan: ID={user.id}, Nama={user.name}, Role={user.role}")
            else:
                print("User tidak ditemukan.")

        elif choice == '4':
            print("\n--- [UPDATE ROLE] ---")
            email = input("Email User yang diupdate: ")
            new_role = input("Role Baru (misal: Organizer_VIP): ")
            update_user_role(email, new_role)

        elif choice == '5':
            print("\n--- [DELETE USER] ---")
            email = input("Email User yang akan dihapus: ")
            delete_user(email)
            
        elif choice == '0':
            print("Keluar dari skrip CRUD.")
            break
        else:
            print("Pilihan tidak valid. Silakan coba lagi.")


if __name__ == "__main__":
    main_menu()