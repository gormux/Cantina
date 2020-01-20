"""empty message

Revision ID: 72a6ae474afc
Revises: 1413593bbd62
Create Date: 2020-01-13 17:01:11.645619

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '72a6ae474afc'
down_revision = '1413593bbd62'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('configuration', sa.Column('config_text', sa.String(length=100), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('configuration', 'config_text')
    # ### end Alembic commands ###
