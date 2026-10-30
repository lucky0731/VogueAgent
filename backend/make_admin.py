"""
Grant or revoke admin access (the `is_admin` flag on a user document).

Usage (from the project folder, with the virtualenv active):

    python -m backend.make_admin                       # list users and who is admin
    python -m backend.make_admin you@example.com       # make this user an admin
    python -m backend.make_admin you@example.com --revoke

The user must already have an account (register on the site or sign in with
Google first). Reload the site afterwards to see the "Manage store" button.
"""
import argparse

from .database import check_connection, users_collection


def list_users() -> None:
    users = list(users_collection.find({}, {"email": 1, "username": 1, "is_admin": 1, "_id": 0}))
    if not users:
        print("No users yet. Register on the site first, then run this again with your email.")
        return
    print(f"{'EMAIL':40} {'USERNAME':20} ADMIN")
    for u in users:
        print(f"{u.get('email', ''):40} {u.get('username', ''):20} {'yes' if u.get('is_admin') else ''}")


def set_admin(email: str, value: bool) -> None:
    email = email.strip().lower()
    result = users_collection.update_one({"email": email}, {"$set": {"is_admin": value}})
    if result.matched_count == 0:
        print(f"No account found for {email}. Register on the site first. Existing users:\n")
        list_users()
        raise SystemExit(1)
    print(f"{email} is {'now an admin' if value else 'no longer an admin'}.")
    if value:
        print("Reload the site to see the 'Manage store' button.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Grant or revoke admin access.")
    parser.add_argument("email", nargs="?", help="email of the account to change")
    parser.add_argument("--revoke", action="store_true", help="remove admin access instead")
    args = parser.parse_args()

    check_connection()
    if args.email:
        set_admin(args.email, not args.revoke)
    else:
        list_users()


if __name__ == "__main__":
    main()
