# =============================================================================
# QMS Platform — Core Package
# =============================================================================
"""
Package central contenant les fondations de l'architecture modulaire.

Ce package fournit :
    - Le gestionnaire de plugins (plugin_manager)
    - Les services partagés (GED, notifications, workflows)
    - Les utilitaires de base (tenant, permissions, audit)

Chaque module métier (haccp, hse, qualite...) est un "plugin" qui s'enregistre
auprès du plugin_manager et peut être activé/désactivé par entreprise.

Usage :
    from app.core import plugin_manager, get_storage, get_bpmn_service
    from app.core import ModuleManifest, register_all_modules

Auteur : QMS Platform Team
Version : 1.0.0
"""

from app.core.plugin_manager import (
    PluginManager,
    ModuleManifest,
    ModuleState,
    plugin_manager,
    module_active,
)

from app.core.storage import StorageService, get_storage
from app.core.bpmn import BpmnService, BpmnParser, BpmnValidator, BpmnGenerator, get_bpmn_service
from app.core.manifests import register_all_modules

__all__ = [
    'PluginManager',
    'ModuleManifest',
    'ModuleState',
    'plugin_manager',
    'module_active',
    'StorageService',
    'get_storage',
    'BpmnService',
    'BpmnParser',
    'BpmnValidator',
    'BpmnGenerator',
    'get_bpmn_service',
    'register_all_modules',
]
