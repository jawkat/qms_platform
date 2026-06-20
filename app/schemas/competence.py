from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.competence import Competence, EmployeCompetence, FormationParticipant

class CompetenceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Competence
        load_instance = True
        include_fk = True

class EmployeCompetenceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = EmployeCompetence
        load_instance = True
        include_fk = True
    
    utilisateur_name = fields.Function(
        lambda obj: f"{obj.utilisateur.prenom} {obj.utilisateur.nom}" if obj.utilisateur else "",
        dump_only=True
    )
    competence_name = fields.Function(
        lambda obj: obj.competence.nom if obj.competence else "",
        dump_only=True
    )
    evalue_par_name = fields.Function(
        lambda obj: f"{obj.evalue_par.prenom} {obj.evalue_par.nom}" if obj.evalue_par else "",
        dump_only=True
    )

class FormationParticipantSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = FormationParticipant
        load_instance = True
        include_fk = True
    
    utilisateur_name = fields.Function(
        lambda obj: f"{obj.utilisateur.prenom} {obj.utilisateur.nom}" if obj.utilisateur else "",
        dump_only=True
    )
    formation_title = fields.Function(
        lambda obj: obj.formation.titre if obj.formation else "",
        dump_only=True
    )
