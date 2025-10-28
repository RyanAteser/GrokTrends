# 2) seed_mock.py  (your mock-data generator)
# Keep your existing mock generator body, just switch the connection:
from connector import get_conn

def main():
    with get_conn() as conn, conn.cursor() as cur:
        # ... paste your existing mock seeding code here ...
        # (unchanged SQL & logic, only the connection wrapper)
        conn.commit()
    print("🎉 Demo data ready!")

if __name__ == "__main__":
    main()
