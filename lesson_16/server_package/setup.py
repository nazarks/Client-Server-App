from setuptools import setup, find_packages

setup(
    name="message_server_april_2023",
    version="0.0.1",
    description="message_server_april_2023",
    author="Sego",
    author_email="grayg@mail.ru",
    # packages=find_packages(),
    packages=["src"],
    install_requires=["PyQt5", "sqlalchemy", "pycryptodome", "pycryptodomex"],
)
