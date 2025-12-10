from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import User

# --- KONFIGURASI KONEKSI ---
# Menggunakan URL koneksi yang sudah diperbarui di alembic.ini
DB_URL = "postgresql://postgres:sigmoid@localhost:5433/ticket_db"

# Inisialisasi Engine
engine = create_engine(DB_URL)

# Buat Session Factory
Session = sessionmaker(bind=engine)


# ===============================================
# OPERASI C: CREATE (Menambahkan Pengguna Baru)
# ===============================================

def add_user(name: str, email: str, password: str, role: str) -> User:
    """Menambahkan user baru ke tabel users."""
    session = Session()
    try:
        # 1. Buat instance objek User baru
        # Catatan: Password HARUS di-hash sebelum disimpan di produksi
        new_user = User(
            name=name,
            email=email,
            password=password, 
            role=role # Harus 'Attendee' atau 'Organizer'
        )

        # 2. Tambahkan objek ke session
        session.add(new_user)

        # 3. Commit (simpan) perubahan ke database
        session.commit()
        
        # Refresh objek untuk mendapatkan ID yang baru dibuat
        session.refresh(new_user)
        print(f"✅ User berhasil ditambahkan. ID: {new_user.id}")
        return new_user

    except Exception as e:
        session.rollback() # Batalkan transaksi jika terjadi error
        print(f"❌ Error saat menambahkan user: {e}")
        return None
    finally:
        session.close()


# ===============================================
# OPERASI R: READ (Membaca Pengguna)
# ===============================================

def get_user_by_email(email: str) -> User | None:
    """Mencari user berdasarkan email."""
    session = Session()
    try:
        user = session.query(User).filter_by(email=email).first()
        return user
    finally:
        session.close()


# ===============================================
# OPERASI U: UPDATE (Memperbarui Role Pengguna)
# ===============================================

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
        print(f"❌ Error saat update user: {e}")
        return False
    finally:
        session.close()


# ===============================================
# OPERASI D: DELETE (Menghapus Pengguna)
# ===============================================

def delete_user(user_id: int) -> bool:
    """Menghapus user berdasarkan ID."""
    session = Session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            session.delete(user)
            session.commit()
            print(f"✅ User dengan ID {user_id} berhasil dihapus.")
            return True
        else:
            print(f"❌ User dengan ID {user_id} tidak ditemukan.")
            return False
    except Exception as e:
        session.rollback()
        print(f"❌ Error saat delete user: {e}")
        return False
    finally:
        session.close()


# ===============================================
# CONTOH PENGGUNAAN
# ===============================================

if __name__ == "__main__":
    print("--- 1. MENAMBAH (CREATE) USER BARU (ATTENDEE) ---")
    attendee = add_user(
        name="Budi Santoso",
        email="budi.santoso@contoh.com",
        password="hashed_attendee_pass",
        role="Attendee"
    )

    print("\n--- 2. MENAMBAH (CREATE) USER BARU (ORGANIZER) ---")
    organizer = add_user(
        name="Event Pro",
        email="event.pro@organizer.com",
        password="hashed_organizer_pass",
        role="Organizer"
    )

    if attendee:
        print(f"\n--- 3. MEMBACA (READ) USER ---")
        found_user = get_user_by_email("budi.santoso@contoh.com")
        if found_user:
            print(f"Ditemukan: ID={found_user.id}, Nama={found_user.name}, Role={found_user.role}")
            
            print(f"\n--- 4. UPDATE ROLE ---")
            update_user_role("budi.santoso@contoh.com", "Attendee_VIP")
            
            print(f"\n--- 5. DELETE USER ---")
            delete_user(found_user.id)