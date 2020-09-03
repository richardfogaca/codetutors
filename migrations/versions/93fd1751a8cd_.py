"""empty message

Revision ID: 93fd1751a8cd
Revises: e68ac86230d7
Create Date: 2020-09-03 15:43:29.840776

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '93fd1751a8cd'
down_revision = 'e68ac86230d7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('reviews', sa.Column('comment', sa.String(length=1500), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('reviews', 'comment')
    # ### end Alembic commands ###
