from models import User


def test_user_password_hashing_behaves_correctly():
    user = User(username="alice", is_admin=False)
    user.set_password("secret123")

    # Hash must not store plaintext
    assert user.password_hash != "secret123"
    assert user.password_hash is not None

    # Correct password verifies successfully
    assert user.check_password("secret123") is True

    # Wrong password is rejected
    assert user.check_password("wrong") is False
    assert user.check_password("") is False
    assert user.check_password("secret123 ") is False


def test_user_password_hash_differs_across_instances():
    # Same plaintext should produce different hashes (bcrypt/scrypt salt)
    u1 = User(username="bob")
    u2 = User(username="carol")
    u1.set_password("password")
    u2.set_password("password")

    assert u1.password_hash != u2.password_hash


def test_user_check_password_after_rehash():
    user = User(username="dave")
    user.set_password("first")
    assert user.check_password("first") is True

    user.set_password("second")
    assert user.check_password("second") is True
    assert user.check_password("first") is False
