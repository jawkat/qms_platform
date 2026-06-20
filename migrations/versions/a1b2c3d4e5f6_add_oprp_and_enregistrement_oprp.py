"""add OPRP type to PRP + create EnregistrementOprp table

Revision ID: a1b2c3d4e5f6
Revises: eac3edf3f2d6
Create Date: 2026-06-19 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = 'eac3edf3f2d6'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to haccp_prp
    with op.batch_alter_table('haccp_prp', schema=None) as batch_op:
        batch_op.add_column(sa.Column('type_prp', sa.String(length=20), server_default='generic', nullable=False))
        batch_op.add_column(sa.Column('processus_id', sa.Integer(), sa.ForeignKey('haccp_processus.id'), nullable=True))
        batch_op.add_column(sa.Column('danger_id', sa.Integer(), sa.ForeignKey('haccp_analyse_danger.id'), nullable=True))
        batch_op.add_column(sa.Column('limite_critique', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('methode_surveillance', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('frequence_surveillance', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('action_corrective', sa.Text(), nullable=True))
        batch_op.create_index(batch_op.f('ix_haccp_prp_type_prp'), ['type_prp'], unique=False)

    # Create EnregistrementOprp table
    op.create_table('haccp_enregistrement_oprp',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entreprise_id', sa.Integer(), nullable=False),
        sa.Column('oprp_id', sa.Integer(), nullable=False),
        sa.Column('date_controle', sa.DateTime(), nullable=False),
        sa.Column('valeur', sa.String(length=100), nullable=False),
        sa.Column('unite', sa.String(length=20), nullable=True),
        sa.Column('conforme', sa.Boolean(), default=True),
        sa.Column('operateur', sa.String(length=100), nullable=True),
        sa.Column('commentaire', sa.Text(), nullable=True),
        sa.Column('action_entreprise', sa.Text(), nullable=True),
        sa.Column('date_creation', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['entreprise_id'], ['entreprise.id'], ),
        sa.ForeignKeyConstraint(['oprp_id'], ['haccp_prp.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('haccp_enregistrement_oprp', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_haccp_enregistrement_oprp_entreprise_id'), ['entreprise_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_haccp_enregistrement_oprp_oprp_id'), ['oprp_id'], unique=False)

    # Set all existing PRPs as type_prp = 'generic'
    op.execute("UPDATE haccp_prp SET type_prp = 'generic'")


def downgrade():
    op.drop_table('haccp_enregistrement_oprp')
    with op.batch_alter_table('haccp_prp', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_haccp_prp_type_prp'))
        batch_op.drop_column('action_corrective')
        batch_op.drop_column('frequence_surveillance')
        batch_op.drop_column('methode_surveillance')
        batch_op.drop_column('limite_critique')
        batch_op.drop_column('danger_id')
        batch_op.drop_column('processus_id')
        batch_op.drop_column('type_prp')
