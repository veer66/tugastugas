"""Populates the database with three fake users.

**Warning:** Storing empty password hashes is a security risk. This script is
intended for demonstration purposes only. In a real application, you
should implement a secure password hashing mechanism.
"""

from tugastugas.database import bind
from tugastugas.models import User

session = bind()

session.add(User(id=1, username='usr1', password_hash=''))
session.add(User(id=2, username='usr2', password_hash=''))
session.add(User(id=3, username='usr3', password_hash=''))

session.commit()
