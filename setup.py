from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in digitz_erp/__init__.py
from digitz_erp import __version__ as version

setup(
	name="digitz_erp",
	version=version,
	description="A simple ERP Software",
	author="Rupesh P",
	author_email="rupeshprajan@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
