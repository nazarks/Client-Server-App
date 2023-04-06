from setuptools import setup, find_packages

setup(
    name="message_client_april_2023",
    version="0.0.1",
    description="Client for message server april 2023",
    author="Sego",
    author_email="grayg@mail.ru",
    # packages=find_packages(),
    packages=["src"],
    install_requires=["PyQt5", "sqlalchemy", "pycryptodome", "pycryptodomex"],
)
