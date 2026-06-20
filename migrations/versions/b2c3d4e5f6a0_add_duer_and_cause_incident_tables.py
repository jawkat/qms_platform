"""add DUER and CauseIncident tables + methode_analyse to incident

Revision ID: b2c3d4e5f6a0
Revises: a1b2c3d4e5f6
Create Date: 2026-06-19 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b2c3d4e5f6a0'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Add methode_analyse to incident
    with op.batch_alter_table('incident', schema=None) as batch_op:
        batch_op.add_column(sa.Column('methode_analyse', sa.String(length=20), server_default='arbre_des_causes', nullable=False))

    # Create unite_travail table
    op.create_table('unite_travail',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entreprise_id', sa.Integer(), nullable=False),
        sa.Column('nom', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('service', sa.String(length=100), nullable=True),
        sa.Column('effectif', sa.Integer(), default=0),
        sa.Column('horaires', sa.String(length=100), nullable=True),
        sa.Column('statut', sa.String(length=20), default='actif'),
        sa.Column('date_creation', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['entreprise_id'], ['entreprise.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('unite_travail', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_unite_travail_entreprise_id'), ['entreprise_id'], unique=False)

    # Create danger_sst table
    op.create_table('danger_sst',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entreprise_id', sa.Integer(), nullable=False),
        sa.Column('unite_travail_id', sa.Integer(), nullable=False),
        sa.Column('famille_danger', sa.String(length=30), nullable=False),
        sa.Column('danger', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=200), nullable=True),
        sa.Column('consequence', sa.Text(), nullable=True),
        sa.Column('mesures_existantes', sa.Text(), nullable=True),
        sa.Column('statut', sa.String(length=20), default='actif'),
        sa.Column('date_creation', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['entreprise_id'], ['entreprise.id'], ),
        sa.ForeignKeyConstraint(['unite_travail_id'], ['unite_travail.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('danger_sst', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_danger_sst_entreprise_id'), ['entreprise_id'], unique=False)

    # Create evaluation_risque_sst table
    op.create_table('evaluation_risque_sst',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entreprise_id', sa.Integer(), nullable=False),
        sa.Column('danger_id', sa.Integer(), nullable=False),
        sa.Column('gravite', sa.Integer(), default=1),
        sa.Column('probabilite', sa.Integer(), default=1),
        sa.Column('frequence', sa.Integer(), default=1),
        sa.Column('maitrise', sa.Integer(), default=1),
        sa.Column('plan_action', sa.Text(), nullable=True),
        sa.Column('responsable_id', sa.Integer(), nullable=True),
        sa.Column('date_echeance', sa.Date(), nullable=True),
        sa.Column('date_revu', sa.Date(), nullable=True),
        sa.Column('statut', sa.String(length=20), default='a_traiter'),
        sa.Column('date_creation', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['entreprise_id'], ['entreprise.id'], ),
        sa.ForeignKeyConstraint(['danger_id'], ['danger_sst.id'], ),
        sa.ForeignKeyConstraint(['responsable_id'], ['utilisateur.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('evaluation_risque_sst', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_evaluation_risque_sst_entreprise_id'), ['entreprise_id'], unique=False)

    # Create cause_incident table
    op.create_table('cause_incident',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entreprise_id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('categorie', sa.String(length=30), default='autre'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('ordre', sa.Integer(), default=0),
        sa.Column('date_creation', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['entreprise_id'], ['entreprise.id'], ),
        sa.ForeignKeyConstraint(['incident_id'], ['incident.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['cause_incident.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('cause_incident', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_cause_incident_entreprise_id'), ['entreprise_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_cause_incident_incident_id'), ['incident_id'], unique=False)


def downgrade():
    op.drop_table('cause_incident')
    op.drop_table('evaluation_risque_sst')
    op.drop_table('danger_sst')
    op.drop_table('unite_travail')
    with op.batch_alter_table('incident', schema=None) as batch_op:
        batch_op.drop_column('methode_analyse')
