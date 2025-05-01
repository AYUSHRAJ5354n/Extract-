from setuptools import setup, find_packages

setup(
    name="dailymotion-extractor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask>=2.0.0",
        "flask-sqlalchemy>=3.0.0",
        "gunicorn>=20.0.0",
        "python-telegram-bot>=20.0.0",
        "requests>=2.25.0",
        "selenium>=4.0.0",
        "trafilatura>=1.0.0",
        "psycopg2-binary>=2.9.0",
        "email-validator>=1.1.0",
        "beautifulsoup4>=4.9.0",
        "lxml>=4.6.0",
        "webdriver-manager>=3.5.0",
    ],
    python_requires=">=3.9",
)