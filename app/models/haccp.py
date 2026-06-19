from app.haccp.models import (
    ProcessusHaccp, ProduitHaccp, MatierePremiere, AnalyseDanger, Ccp,
    EnregistrementCcp, Prp,
    TracabiliteLot, RappelProduit,
    produit_processus, TypeDanger, StatutHaccp
)
from .partages import Fournisseur, Formation, Reclamation

# backward-compat aliases pour les routes haccp existantes
FournisseurHaccp = Fournisseur
FormationHaccp = Formation
ReclamationHaccp = Reclamation
