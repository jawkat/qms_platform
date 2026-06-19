from .auth import Permission, RolePermission, Role, EntrepriseRole, Utilisateur
from .entreprise import Entreprise, HistoriquePaiement, SubscriptionPlan, Secteur, EntrepriseSecteur
from .actions import ActionStatusEnum, ActionCorrective
from .proofs import ProofMaster, ProofReference
from .ged import Dossier, TypeDocument, WorkflowLog, HistoriqueDocument
from .conformite import ExigenceType, NiveauRisqueType, ApplicabiliteEnum, ConformiteEnum, EntrepriseTexte, EvaluationArticle, HistoriqueEvaluation
from .textes import Domaine, TexteReglementaire, TexteVersion, Article
from .audit import Audit, AuditObservation, ChecklistModele, ChecklistItem, AuditChecklistReponse
from .indicateurs import Indicateur, IndicateurValeur
from .ticket import Ticket, MessageTicket
from .systeme import Notification, JournalSecurite, TacheSysteme
from .demo import Disponibilite, CreneauDemo
from .partages import Fournisseur, Formation, Reclamation
from .qualite import (Risque, Equipement, ControleQualite, RevueDirection)
from .nonconformite import NonConformite
from .hse import Incident, EPI, Inspection, InspectionItem, PermisTravail
from .ishikawa import AnalyseIshikawa, CauseIshikawa
from .competence import Competence, FormationParticipant
from .historique_fournisseur import EvaluationFournisseur, HistoriqueFournisseur
from .echeancier import ObligationReglementaire
from .veille import SourceReglementaire, Veille
from .haccp import *

# Nouveaux modules (8 modules manquants)
from app.environnement.models import AspectEnvironnemental, SuiviEnvironnemental
from app.maintenance.models import EquipementMaintenance, InterventionMaintenance
from app.laboratoire.models import PlanAnalyse, Echantillon, ResultatAnalyse
from app.planification.models import EvenementPlanification
from app.reunions.models import Reunion, CompteRendu, ActionReunion
from app.rh_qhse.models import EmployeQHSE
from app.connaissances.models import REX, FAQ
from app.urgences.models import PlanUrgence, ExerciceEvacuation, MainCourante

# backward-compatible aliases pour migration progressive des routes
ReclamationClient = Reclamation
FournisseurHaccp = Fournisseur
FormationHaccp = Formation
