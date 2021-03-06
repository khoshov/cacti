"""Add difficulty field.

Revision ID: 867b33c605ab
Revises: c64eaeac6b5a
Create Date: 2022-06-18 11:55:25.248402

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
from app import Cactus


# revision identifiers, used by Alembic.
revision = '867b33c605ab'
down_revision = 'c64eaeac6b5a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('cactus', sa.Column('difficulty', sqlalchemy_utils.types.choice.ChoiceType(Cactus.DIFFICULTY), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('cactus', 'difficulty')
    # ### end Alembic commands ###
