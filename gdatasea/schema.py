from eralchemy2 import render_er
from gdatasea.database import GDATASEA_DB

def generate_svg():
    render_er(
        GDATASEA_DB, "./gdatasea_db.svg", exclude_tables=["alembic_version"]
    )

if __name__ == '__main__':
    generate_svg()
