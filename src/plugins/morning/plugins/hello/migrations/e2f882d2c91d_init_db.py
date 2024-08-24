"""init db

修订 ID: e2f882d2c91d
父修订:
创建时间: 2023-10-29 11:31:30.118819

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e2f882d2c91d"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = ("hello",)
depends_on: str | Sequence[str] | None = None


def upgrade(name: str = "") -> None:
    if name:
        return
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "hello_hello",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "target",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=False,
        ),
        sa.Column("bot_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_hello_hello")),
        info={"bind_key": "hello"},
    )
    # ### end Alembic commands ###


def downgrade(name: str = "") -> None:
    if name:
        return
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("hello_hello")
    # ### end Alembic commands ###
