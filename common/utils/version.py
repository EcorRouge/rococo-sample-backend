import tomllib
import os

# Locate the correct pyproject.toml (flask/pyproject.toml)
# common/utils/version.py -> common/utils -> common -> root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLASK_TOML = os.path.join(BASE_DIR, 'flask', 'pyproject.toml')

target_file = FLASK_TOML if os.path.exists(FLASK_TOML) else 'pyproject.toml'

with open(target_file, 'rb') as f:
    pyproject_data = tomllib.load(f)


def get_service_version():
    return pyproject_data['tool']['poetry']['version']


def get_project_name():
    return pyproject_data['tool']['poetry']['name'].title()


def main():
    print(f"{get_project_name()} running at version: {get_service_version()}")
