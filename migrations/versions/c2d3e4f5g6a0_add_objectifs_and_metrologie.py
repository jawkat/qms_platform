"""add ObjectifQualite, EnregistrementEtalonnage, metrology fields to equipement

Revision ID: c2d3e4f5g6a0
Revises: b2c3d4e5f6a0
Create Date: 2026-06-19 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c2d3e4f5g6a0'
down_revision = 'b2c3d4e5f6a0'
branch_labels = None
depends_on = None


def upgrade():
    # ObjectifQualite
    op.create_table('objectif_qualite',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entreprise_id', sa.Integer(), nullable=False),
        sa.Column('titre', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('indicateur_id', sa.Integer(), nullable=True),
        sa.Column('cible', sa.Float(), nullable=True),
        sa.Column('seuil_alerte', sa.Float(), nullable=True),
        sa.Column('pilote_id', sa.Integer(), nullable=True),
        sa.Column('date_debut', sa.Date(), nullable=True),
        sa.Column('date_echeance', sa.Date(), nullable=True),
        sa.Column('statut', sa.String(length=20), nullable=True, server_default='en_cours'),
        sa.Column('domaine', sa.String(length=20), nullable=True, server_default='qualite'),
        sa.Column('processus_concerne', sa.String(length=200), nullable=True),
        sa.Column('date_creation', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['entreprise_id'], ['entreprise.id'], ),
        sa.ForeignKeyConstraint(['indicateur_id'], ['indicateur.id'], ),
        sa.ForeignKeyConstraint(['pilote_id'], ['utilisateur.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('objectif_qualite', schema=None) as batch_op:
        batch_op.create_index('ix_objectif_qualite_entreprise', ['entreprise_id'])

    # Add metrology fields to equipement
    with op.batch_alter_table('equipement', schema=None) as batch_op:
        batch_op.add_column(sa.Column('type_equipement', sa.String(length=30), server_default='production', nullable=True))
        batch_op.add_column(sa.Column('frequence_etalonnage_jours', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('precision', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('unite_mesure', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('tolerance_min', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('tolerance_max', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('date_dernier_etalonnage', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('date_prochain_etalonnage', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('organisme_etalonnage', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('certificat_etalonnage', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('statut_metrologique', sa.String(length=20), server_default='en_cours', nullable=True))

    # EnregistrementEtalonnage
    op.create_table('enregistrement_etalonnage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entreprise_id', sa.Integer(), nullable=False),
        sa.Column('equipement_id', sa.Integer(), nullable=False),
        sa.Column('date_etalonnage', sa.Date(), nullable=False),
        sa.Column('valeur_mesuree', sa.Float(), nullable=True),
        sa.Column('valeur_reference', sa.Float(), nullable=True),
        sa.Column('ecart', sa.Float(), nullable=True),
        sa.Column('conforme', sa.Boolean(), nullable=True, server_default=sa.text('true')),
        sa.Column('certificat_id', sa.String(length=100), nullable=True),
        sa.Column('operateur', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('date_creation', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['entreprise_id'], ['entreprise.id'], ),
        sa.ForeignKeyConstraint(['equipement_id'], ['equipement.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('enregistrement_etalonnage', schema=None) as batch_op:
        batch_op.create_index('ix_enreg_etalonnage_equip', ['equipement_id'])
        batch_op.create_index('ix_enreg_etalonnage_entreprise', ['entreprise_id'])


def downgrade():
    op.drop_table('enregistrement_etalonnage')
    with op.batch_alter_table('equipement', schema=None) as batch_op:
        batch_op.drop_column('statut_metrologique')
        batch_op.drop_column('certificat_etalonnage')
        batch_op.drop_column('organisme_etalonnage')
        batch_op.drop_column('date_prochain_etalonnage')
        batch_op.drop_column('date_dernier_etalonnage')
        batch_op.drop_column('tolerance_max')
        batch_op.drop_column('tolerance_min')
        batch_op.drop_column('unite_mesure')
        batch_op.drop_column('precision')
        batch_op.drop_column('frequence_etalonnage_jours')
        batch_op.drop_column('type_equipement')
    op.drop_table('objectif_qualite')
