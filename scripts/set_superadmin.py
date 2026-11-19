"""Script to ensure akpodomagoodluck7@gmail.com is configured as Super Admin."""
import sys
from pathlib import Path

# Add backend to sys.path
backend_path = Path(__file__).resolve().parent.parent / "saas-dashboard" / "backend"
sys.path.insert(0, str(backend_path))

from main import get_dev_db, get_supabase_admin, get_supabase, _fetch_user_role

def main():
    target_email = "akpodomagoodluck7@gmail.com"
    print(f"Setting role for {target_email} to super_admin...")

    # 1. Update SQLite dev_users
    conn = get_dev_db()
    if conn:
        cur = conn.cursor()
        cur.execute("UPDATE dev_users SET role = 'super_admin' WHERE LOWER(email) = LOWER(?)", (target_email,))
        conn.commit()
        rows = cur.execute("SELECT id, email, role FROM dev_users WHERE LOWER(email) = LOWER(?)", (target_email,)).fetchall()
        print("Dev DB rows:", rows)

    # 2. Update Supabase public.users if table exists
    admin = get_supabase_admin() or get_supabase()
    if admin:
        try:
            admin.table("users").update({"role": "super_admin"}).ilike("email", target_email).execute()
            print("Updated Supabase public.users role to super_admin")
        except Exception as e:
            print(f"Note: Supabase table update skipped or not present: {e}")

    # 3. Test role resolution
    resolved = _fetch_user_role("dummy-id", target_email)
    print(f"Verified resolved role for {target_email}: {resolved}")

if __name__ == "__main__":
    main()

