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
from .competence import Competence, FormationParticipant, EmployeCompetence
from .historique_fournisseur import EvaluationFournisseur, HistoriqueFournisseur
from .echeancier import ObligationReglementaire
from .veille import SourceReglementaire, Veille
from .haccp import (
    TypeDanger, StatutHaccp, ProcessusHaccp, ProduitHaccp, MatierePremiere,
    AnalyseDanger, Ccp, EnregistrementCcp, Prp, EnregistrementOprp,
    TracabiliteLot, RappelProduit
)

# Nouveaux modules centralisés
from .environnement import AspectEnvironnemental, SuiviEnvironnemental
from .maintenance import EquipementMaintenance, InterventionMaintenance
from .laboratoire import PlanAnalyse, Echantillon, ResultatAnalyse
from .planification import EvenementPlanification
from .reunions import Reunion, CompteRendu, ActionReunion
from .rh_qhse import EmployeQHSE
from .connaissances import REX, FAQ
from .urgences import PlanUrgence, ExerciceEvacuation, MainCourante
from .change_management import ChangeRequest
from .processus import Processus, IndicateurProcessus
from .workflow_engine import WorkflowModele, WorkflowEtape, WorkflowInstance, WorkflowHistorique

# backward-compatible aliases pour migration progressive des routes
ReclamationClient = Reclamation
FournisseurHaccp = Fournisseur
FormationHaccp = Formation
