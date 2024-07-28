"""add subtitles_option

Revision ID: 6059af1c9d15
Revises: 728b8e1eff7c
Create Date: 2024-07-26 20:00:29.532476

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6059af1c9d15'
down_revision: Union[str, None] = '728b8e1eff7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('options', sa.Column('subtitles', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('options', 'subtitles')
    # ### end Alembic commands ###
