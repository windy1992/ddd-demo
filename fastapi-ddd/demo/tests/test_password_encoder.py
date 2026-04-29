from demo.util.password.encoder import PasswordEncoder


def test_encoder():
    PasswordEncoder.encode(b"test")
