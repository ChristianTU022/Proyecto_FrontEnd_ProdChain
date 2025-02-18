import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://connectorsql:connectorsql@localhost/prodchain'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.urandom(24)

