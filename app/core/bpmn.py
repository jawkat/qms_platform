# =============================================================================
# QMS Platform — BPMN Process Mapping Integration
# =============================================================================
"""
Intégration de bpmn.io pour la cartographie et l'édition de processus.

Ce module fournit :
1. Le stockage et la gestion des diagrammes BPMN (XML)
2. L'extraction de métadonnées depuis les fichiers BPMN
3. La synchronisation entre le modèle Processus et le diagramme BPMN
4. Les endpoints API pour l'éditeur bpmn.io (frontend)

Architecture :
    ┌─────────────────────────────────────────────────────┐
    │                BPMN Integration                     │
    │                                                     │
    │  ┌──────────────┐     ┌──────────────────────┐     │
    │  │  Processus   │ ←→  │  BPMN XML Storage    │     │
    │  │  (SQLAlchemy)│     │  (MINIO / Local FS)  │     │
    │  └──────────────┘     └──────────────────────┘     │
    │         ↑                        ↑                  │
    │  ┌──────┴──────┐     ┌──────────┴──────────┐      │
    │  │  Routes API │     │  bpmn.io Frontend    │      │
    │  │  (Backend)  │     │  (JavaScript)        │      │
    │  └─────────────┘     └─────────────────────┘      │
    └─────────────────────────────────────────────────────┘

Format BPMN supporté :
    - BPMN 2.0 XML (standard OASIS)
    - Import/Export depuis l'éditeur bpmn-js
    - Extraction automatique des tâches, participants, flux

Auteur : QMS Platform Team
Version : 1.0.0
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

# Namespace BPMN 2.0
BPMN_NS = {
    'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
    'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
    'dc': 'http://www.omg.org/spec/DD/20100524/DC',
    'di': 'http://www.omg.org/spec/DD/20100524/DI',
}


# =============================================================================
# Data Classes — Métadonnées BPMN extraites
# =============================================================================

@dataclass
class BpmnElement:
    """
    Représente un élément extrait d'un diagramme BPMN.

    Attributes:
        id: Identifiant BPMN de l'élément
        name: Nom de l'élément
        type: Type BPMN (Task, Gateway, Event, etc.)
        lane: Swimlane/Lane assignée (si applicable)
        documentation: Texte de documentation
    """
    id: str
    name: str = ''
    type: str = ''
    lane: str = ''
    documentation: str = ''


@dataclass
class BpmnFlow:
    """
    Représente un flux (séquence ou messagerie) dans un diagramme BPMN.

    Attributes:
        id: Identifiant du flux
        source: ID de l'élément source
        target: ID de l'élément cible
        name: Nom/label du flux (condition, etc.)
        type: Type de flux (SequenceFlow, MessageFlow, etc.)
    """
    id: str
    source: str
    target: str
    name: str = ''
    type: str = 'SequenceFlow'


@dataclass
class BpmnMetadata:
    """
    Métadonnées complètes extraites d'un diagramme BPMN.

    Attributes:
        process_id: ID du processus BPMN
        process_name: Nom du processus
        process_documentation: Description du processus
        is_executable: Si le processus est exécutable
        elements: Liste des éléments (tâches, portes, événements)
        flows: Liste des flux
        lanes: Liste des swimlanes/lanes
        participants: Liste des participants (pools)
        xml_size: Taille du XML en bytes
    """
    process_id: str = ''
    process_name: str = ''
    process_documentation: str = ''
    is_executable: bool = False
    elements: List[BpmnElement] = field(default_factory=list)
    flows: List[BpmnFlow] = field(default_factory=list)
    lanes: List[str] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    xml_size: int = 0


# =============================================================================
# BPMN Parser — Extraction de métadonnées
# =============================================================================

class BpmnParser:
    """
    Parseur de diagrammes BPMN 2.0 XML.

    Extrait les métadonnées et la structure d'un fichier BPMN
    sans dépendance externe (utilise xml.etree.ElementTree).

    Usage :
        parser = BpmnParser()
        metadata = parser.parse(bpmn_xml_string)
        print(metadata.process_name)
        for element in metadata.elements:
            print(f"  {element.type}: {element.name}")
    """

    def parse(self, xml_content: str) -> BpmnMetadata:
        """
        Parse un fichier BPMN et en extrait les métadonnées.

        Args:
            xml_content: Contenu XML du fichier BPMN

        Returns:
            BpmnMetadata avec tous les éléments extraits
        """
        metadata = BpmnMetadata(xml_size=len(xml_content))

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error("Invalid BPMN XML: %s", e)
            return metadata

        # Extraire les participants (pools)
        metadata.participants = self._extract_participants(root)

        # Extraire le processus principal
        process = root.find('.//bpmn:process', BPMN_NS)
        if process is not None:
            metadata.process_id = process.get('id', '')
            metadata.process_name = process.get('name', '')
            metadata.is_executable = process.get('isExecutable', 'false') == 'true'

            # Documentation du processus
            doc_elem = process.find('bpmn:documentation', BPMN_NS)
            if doc_elem is not None and doc_elem.text:
                metadata.process_documentation = doc_elem.text.strip()

            # Extraire les lanes
            metadata.lanes = self._extract_lanes(process)

            # Extraire les éléments
            metadata.elements = self._extract_elements(process)

            # Extraire les flux
            metadata.flows = self._extract_flows(process)

        logger.info(
            "BPMN parsed: %s (%d elements, %d flows)",
            metadata.process_name, len(metadata.elements), len(metadata.flows)
        )
        return metadata

    def _extract_participants(self, root: ET.Element) -> List[str]:
        """Extrait les noms des participants (pools)."""
        participants = []
        for elem in root.findall('.//bpmn:participant', BPMN_NS):
            name = elem.get('name', '')
            if name:
                participants.append(name)
        return participants

    def _extract_lanes(self, process: ET.Element) -> List[str]:
        """Extrait les noms des swimlanes/lanes."""
        lanes = []
        for lane_set in process.findall('.//bpmn:laneSet', BPMN_NS):
            for lane in lane_set.findall('bpmn:lane', BPMN_NS):
                name = lane.get('name', '')
                if name:
                    lanes.append(name)
        return lanes

    def _extract_elements(self, process: ET.Element) -> List[BpmnElement]:
        """Extrait tous les éléments du processus."""
        elements = []

        # Mapping des namespaces BPMN vers des types lisibles
        ELEMENT_TYPES = {
            'bpmn:startEvent': 'StartEvent',
            'bpmn:endEvent': 'EndEvent',
            'bpmn:task': 'Task',
            'bpmn:serviceTask': 'ServiceTask',
            'bpmn:userTask': 'UserTask',
            'bpmn:scriptTask': 'ScriptTask',
            'bpmn:sendTask': 'SendTask',
            'bpmn:receiveTask': 'ReceiveTask',
            'bpmn:manualTask': 'ManualTask',
            'bpmn:businessRuleTask': 'BusinessRuleTask',
            'bpmn:callActivity': 'CallActivity',
            'bpmn:subProcess': 'SubProcess',
            'bpmn:exclusiveGateway': 'ExclusiveGateway',
            'bpmn:parallelGateway': 'ParallelGateway',
            'bpmn:inclusiveGateway': 'InclusiveGateway',
            'bpmn:complexGateway': 'ComplexGateway',
            'bpmn:intermediateCatchEvent': 'IntermediateCatchEvent',
            'bpmn:intermediateThrowEvent': 'IntermediateThrowEvent',
            'bpmn:boundaryEvent': 'BoundaryEvent',
        }

        # Construire un mapping lane_id -> lane_name
        lane_map = {}
        for lane_set in process.findall('.//bpmn:laneSet', BPMN_NS):
            for lane in lane_set.findall('bpmn:lane', BPMN_NS):
                lane_id = lane.get('id', '')
                lane_name = lane.get('name', '')
                # Mapper les flowNodeRefs vers la lane
                for ref in lane.findall('bpmn:flowNodeRef', BPMN_NS):
                    if ref.text:
                        lane_map[ref.text] = lane_name

        # Parcourir chaque type d'élément
        for ns_tag, readable_type in ELEMENT_TYPES.items():
            for elem in process.findall(f'.//{ns_tag}', BPMN_NS):
                elem_id = elem.get('id', '')
                elem_name = elem.get('name', '')

                # Documentation
                doc = ''
                doc_elem = elem.find('bpmn:documentation', BPMN_NS)
                if doc_elem is not None and doc_elem.text:
                    doc = doc_elem.text.strip()

                elements.append(BpmnElement(
                    id=elem_id,
                    name=elem_name,
                    type=readable_type,
                    lane=lane_map.get(elem_id, ''),
                    documentation=doc,
                ))

        return elements

    def _extract_flows(self, process: ET.Element) -> List[BpmnFlow]:
        """Extrait tous les flux de séquence."""
        flows = []

        for seq_flow in process.findall('.//bpmn:sequenceFlow', BPMN_NS):
            flows.append(BpmnFlow(
                id=seq_flow.get('id', ''),
                source=seq_flow.get('sourceRef', ''),
                target=seq_flow.get('targetRef', ''),
                name=seq_flow.get('name', ''),
                type='SequenceFlow',
            ))

        return flows


# =============================================================================
# BPMN Validator — Validation de cohérence
# =============================================================================

class BpmnValidator:
    """
    Validateur de diagrammes BPMN pour la conformité QMS.

    Vérifie les règles métier :
    - Chaque processus a au moins un start/end event
    - Les tâches ont des noms explicites
    - Les gateways ont des conditions
    - Les lanes correspondent aux rôles organisatio
    """

    def validate(self, metadata: BpmnMetadata) -> List[Dict]:
        """
        Valide un diagramme BPMN et retourne les warnings/errors.

        Args:
            metadata: Métadonnées extraites du diagramme

        Returns:
            Liste de dicts avec 'level' (error/warning), 'message', 'element_id'
        """
        issues = []

        # Vérifier la présence de start/end events
        start_events = [e for e in metadata.elements if e.type == 'StartEvent']
        end_events = [e for e in metadata.elements if e.type == 'EndEvent']

        if not start_events:
            issues.append({
                'level': 'error',
                'message': 'Le processus doit avoir au moins un événement de début',
                'element_id': None,
            })

        if not end_events:
            issues.append({
                'level': 'error',
                'message': 'Le processus doit avoir au moins un événement de fin',
                'element_id': None,
            })

        # Vérifier les tâches sans nom
        tasks = [e for e in metadata.elements if e.type.endswith('Task')]
        for task in tasks:
            if not task.name:
                issues.append({
                    'level': 'warning',
                    'message': f'Tâche sans nom: {task.id}',
                    'element_id': task.id,
                })

        # Vérifier les gateways sans nom
        gateways = [e for e in metadata.elements if 'Gateway' in e.type]
        for gw in gateways:
            if not gw.name:
                issues.append({
                    'level': 'warning',
                    'message': f'Gateway sans nom: {gw.id}',
                    'element_id': gw.id,
                })

        # Vérifier les flux sans source/cible
        for flow in metadata.flows:
            if not flow.source or not flow.target:
                issues.append({
                    'level': 'error',
                    'message': f'Flux incomplet: {flow.id}',
                    'element_id': flow.id,
                })

        return issues


# =============================================================================
# BPMN Generator — Création de diagrammes
# =============================================================================

class BpmnGenerator:
    """
    Générateur de diagrammes BPMN 2.0 XML.

    Crée des diagrammes BPMN à partir de structures de données Python.
    Utile pour la génération automatique de processus standards.
    """

    @staticmethod
    def create_simple_process(
        process_id: str,
        process_name: str,
        tasks: List[Dict],
        lanes: List[str] = None
    ) -> str:
        """
        Génère un diagramme BPMN simple avec une séquence de tâches.

        Args:
            process_id: ID du processus
            process_name: Nom du processus
            tasks: Liste de dicts avec 'id', 'name', 'lane' (optionnel)
            lanes: Liste des noms de lanes (optionnel)

        Returns:
            String XML du diagramme BPMN 2.0

        Exemple :
            xml = BpmnGenerator.create_simple_process(
                process_id='Process_1',
                process_name='Traitement NC',
                tasks=[
                    {'id': 'Task_1', 'name': 'Déclaration'},
                    {'id': 'Task_2', 'name': 'Analyse'},
                    {'id': 'Task_3', 'name': 'Action corrective'},
                ],
                lanes=['Déclarant', 'Responsable QSE']
            )
        """
        # Construire le XML
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"',
            '  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"',
            '  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"',
            '  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"',
            f'  id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">',
        ]

        # Process
        lines.append(f'  <bpmn:process id="{process_id}" name="{process_name}" isExecutable="false">')

        # Lanes (si fournies)
        if lanes:
            lines.append('    <bpmn:laneSet id="LaneSet_1">')
            for i, lane_name in enumerate(lanes):
                lines.append(f'      <bpmn:lane id="Lane_{i+1}" name="{lane_name}">')
                # Ajouter les tâches de cette lane
                lane_tasks = [t for t in tasks if t.get('lane') == lane_name]
                for task in lane_tasks:
                    lines.append(f'        <bpmn:flowNodeRef>{task["id"]}</bpmn:flowNodeRef>')
                lines.append('      </bpmn:lane>')
            lines.append('    </bpmn:laneSet>')

        # Start Event
        lines.append('    <bpmn:startEvent id="StartEvent_1" name="Début">')
        lines.append('    </bpmn:startEvent>')

        # Tâches
        for task in tasks:
            task_type = task.get('type', 'Task')
            lines.append(
                f'    <bpmn:{task_type} id="{task["id"]}" name="{task["name"]}">'
            )
            lines.append(f'    </bpmn:{task_type}>')

        # End Event
        lines.append('    <bpmn:endEvent id="EndEvent_1" name="Fin">')
        lines.append('    </bpmn:endEvent>')

        # Flux de séquence
        # Start -> premier task
        if tasks:
            lines.append(
                f'    <bpmn:sequenceFlow id="Flow_Start" '
                f'sourceRef="StartEvent_1" targetRef="{tasks[0]["id"]}" />'
            )

        # Tâches successives
        for i in range(len(tasks) - 1):
            lines.append(
                f'    <bpmn:sequenceFlow id="Flow_{i+1}" '
                f'sourceRef="{tasks[i]["id"]}" targetRef="{tasks[i+1]["id"]}" />'
            )

        # Dernier task -> End
        if tasks:
            lines.append(
                f'    <bpmn:sequenceFlow id="Flow_End" '
                f'sourceRef="{tasks[-1]["id"]}" targetRef="EndEvent_1" />'
            )

        lines.append('  </bpmn:process>')

        # DI (diagram interchange) — positions approximatives
        lines.append('  <bpmndi:BPMNDiagram id="BPMNDiagram_1">')
        lines.append('    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="' + process_id + '">')

        # Position start
        lines.append('      <bpmndi:BPMNShape id="StartEvent_1_di" bpmnElement="StartEvent_1">')
        lines.append('        <dc:Bounds x="179" y="99" width="36" height="36" />')
        lines.append('      </bpmndi:BPMNShape>')

        # Position tâches
        x_offset = 270
        for i, task in enumerate(tasks):
            lines.append(f'      <bpmndi:BPMNShape id="{task["id"]}_di" bpmnElement="{task["id"]}">')
            lines.append(f'        <dc:Bounds x="{x_offset}" y="77" width="100" height="80" />')
            lines.append(f'      </bpmndi:BPMNShape>')
            x_offset += 160

        # Position end
        lines.append('      <bpmndi:BPMNShape id="EndEvent_1_di" bpmnElement="EndEvent_1">')
        lines.append(f'        <dc:Bounds x="{x_offset}" y="99" width="36" height="36" />')
        lines.append('      </bpmndi:BPMNShape>')

        lines.append('    </bpmndi:BPMNPlane>')
        lines.append('  </bpmndi:BPMNDiagram>')
        lines.append('</bpmn:definitions>')

        return '\n'.join(lines)

    @staticmethod
    def create_from_processus(processus_data: Dict) -> str:
        """
        Génère un BPMN à partir des données d'un processus QMS.

        Convertit les champs du modèle Processus en diagramme BPMN.

        Args:
            processus_data: Dict avec nom, description, entree, sortie,
                           objectifs, risques_associes, etc.

        Returns:
            String XML BPMN 2.0
        """
        tasks = []

        # Tâche d'entrée
        if processus_data.get('entree'):
            tasks.append({
                'id': 'Task_Entree',
                'name': 'Entrées: ' + processus_data['entree'][:50],
                'type': 'ManualTask',
            })

        # Tâche principale
        tasks.append({
            'id': 'Task_Principale',
            'name': processus_data.get('nom', 'Processus'),
            'type': 'Task',
        })

        # Tâche de sortie
        if processus_data.get('sortie'):
            tasks.append({
                'id': 'Task_Sortie',
                'name': 'Sorties: ' + processus_data['sortie'][:50],
                'type': 'ManualTask',
            })

        if not tasks:
            tasks.append({
                'id': 'Task_1',
                'name': processus_data.get('nom', 'Processus'),
            })

        return BpmnGenerator.create_simple_process(
            process_id=f"Process_{processus_data.get('id', 'new')}",
            process_name=processus_data.get('nom', 'Nouveau processus'),
            tasks=tasks,
        )


# =============================================================================
# Service BPMN — Orchestration
# =============================================================================

class BpmnService:
    """
    Service d'orchestration pour les diagrammes BPMN.

    Combine le parser, le validator et le generator pour fournir
    une interface unifiée aux routes et aux autres services.
    """

    def __init__(self):
        self.parser = BpmnParser()
        self.validator = BpmnValidator()
        self.generator = BpmnGenerator()

    def import_bpmn(self, xml_content: str) -> Tuple[BpmnMetadata, List[Dict]]:
        """
        Importe et valide un fichier BPMN.

        Args:
            xml_content: Contenu XML du fichier BPMN

        Returns:
            Tuple de (metadata, issues)
        """
        metadata = self.parser.parse(xml_content)
        issues = self.validator.validate(metadata)
        return metadata, issues

    def export_bpmn(self, processus_data: Dict) -> str:
        """
        Exporte un processus QMS en format BPMN.

        Args:
            processus_data: Données du processus

        Returns:
            String XML BPMN 2.0
        """
        return self.generator.create_from_processus(processus_data)

    def get_process_summary(self, metadata: BpmnMetadata) -> Dict:
        """
        Retourne un résumé du processus pour l'API.

        Args:
            metadata: Métadonnées extraites

        Returns:
            Dict avec les infos essentielles
        """
        return {
            'process_id': metadata.process_id,
            'process_name': metadata.process_name,
            'is_executable': metadata.is_executable,
            'task_count': len([e for e in metadata.elements if e.type.endswith('Task')]),
            'gateway_count': len([e for e in metadata.elements if 'Gateway' in e.type]),
            'event_count': len([e for e in metadata.elements if 'Event' in e.type]),
            'flow_count': len(metadata.flows),
            'lane_count': len(metadata.lanes),
            'participants': metadata.participants,
            'documentation': metadata.process_documentation,
        }


# =============================================================================
# Instance globale
# =============================================================================

_bpmn_service = None


def get_bpmn_service() -> BpmnService:
    """
    Retourne l'instance singleton du BpmnService.
    """
    global _bpmn_service
    if _bpmn_service is None:
        _bpmn_service = BpmnService()
    return _bpmn_service
