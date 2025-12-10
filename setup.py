from setuptools import setup, find_packages

setup(
    name='ticket-system-core',
    version='1.0.0',
    description='Core Database Models for Ticket System',
    packages=find_packages(), # Ini akan mendeteksi folder 'ticket_system_core'
    include_package_data=True,
    package_data={
        'ticket_system_core': ['alembic.ini', 'alembic/*']
    },
    install_requires=[
        'SQLAlchemy',
        'alembic',
        'psycopg2-binary',
        'bcrypt'
    ],
)