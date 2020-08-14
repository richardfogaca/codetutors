"""empty message

Revision ID: f2e02577c86e
Revises: 
Create Date: 2020-08-13 11:16:04.772159

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f2e02577c86e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('first_name', sa.VARCHAR(length=64), autoincrement=False, nullable=False),
    sa.Column('last_name', sa.VARCHAR(length=64), autoincrement=False, nullable=False),
    sa.Column('email', sa.VARCHAR(length=120), autoincrement=False, nullable=False),
    sa.Column('profile_img', sa.VARCHAR(length=120), autoincrement=False, nullable=True),
    sa.Column('password_hash', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('timestamp_joined', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='users_pkey')
    )
    op.create_table('categories',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(length=64), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='categories_pkey')
    )
    op.create_table('tutors',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('price', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='tutors_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='tutors_pkey')
    )
    op.create_table('tutor_category',
    sa.Column('tutor_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('category_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], name='tutor_category_category_id_fkey'),
    sa.ForeignKeyConstraint(['tutor_id'], ['tutors.id'], name='tutor_category_tutor_id_fkey'),
    sa.PrimaryKeyConstraint('tutor_id', 'category_id', name='tutor_category_pkey')
    )
    op.create_index('ix_categories_name', 'categories', ['name'], unique=False)
    op.create_table('reviews',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('tutor_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('rating', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('timestamp', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['tutor_id'], ['tutors.id'], name='reviews_tutor_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='reviews_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='reviews_pkey')
    )
    op.create_index('ix_reviews_timestamp', 'reviews', ['timestamp'], unique=False)
    op.create_index('ix_reviews_rating', 'reviews', ['rating'], unique=False)
    
    
    op.create_index('ix_users_timestamp_joined', 'users', ['timestamp_joined'], unique=False)
    op.create_index('ix_users_last_name', 'users', ['last_name'], unique=False)
    op.create_index('ix_users_first_name', 'users', ['first_name'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_first_name', table_name='users')
    op.drop_index('ix_users_last_name', table_name='users')
    op.drop_index('ix_users_timestamp_joined', table_name='users')
    op.drop_table('users')
    op.drop_table('tutors')
    op.drop_index('ix_reviews_rating', table_name='reviews')
    op.drop_index('ix_reviews_timestamp', table_name='reviews')
    op.drop_table('reviews')
    op.drop_index('ix_categories_name', table_name='categories')
    op.drop_table('categories')
    op.drop_table('tutor_category')
    # ### end Alembic commands ###
