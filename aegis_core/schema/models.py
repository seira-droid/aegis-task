"""
Intermediate Knowledge Representation (IKR) Schema
Aegis Knowledge Ingestion Challenge
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class TrustLevel(str, Enum):
    ENGINEERING_BULLETIN = "ENGINEERING_BULLETIN"  # Authoritative ECN, machine exports (weight: 1.0)
    OFFICIAL_MANUAL = "OFFICIAL_MANUAL"            # Clean manuals, alarm refs, schematics (weight: 0.85)
    FIELD_RECORD_LOW_TRUST = "FIELD_RECORD_LOW_TRUST" # Uncontrolled scans, informal notes (weight: 0.40)
    NOISE_EXTERNAL = "NOISE_EXTERNAL"              # Irrelevant MSDS, outside docs (weight: 0.10)


class FactStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    CONTRADICTED = "CONTRADICTED"
    UNVERIFIED = "UNVERIFIED"


class EpistemicStatus(str, Enum):
    DEFINITIVE = "DEFINITIVE"                  # Unambiguous answer supported by current authoritative docs
    VERSION_SCOPED = "VERSION_SCOPED"          # Answer depends on software/hardware revision
    CONFLICT_RESOLVED = "CONFLICT_RESOLVED"    # Disagreement exists between sources, resolved by trust/order
    UNANSWERABLE_GAP = "UNANSWERABLE_GAP"      # Question asks for facts absent from dataset (no hallucination)
    FALSE_PREMISE = "FALSE_PREMISE"            # Question presupposes nonexistent components or relations


class EntityType(str, Enum):
    COMPONENT = "COMPONENT"
    ALARM = "ALARM"
    CONTROLLER = "CONTROLLER"
    SUBSYSTEM = "SUBSYSTEM"
    PARAMETER = "PARAMETER"
    DOCUMENT = "DOCUMENT"


class SourceDocument(BaseModel):
    id: str
    filename: str
    file_type: str
    trust_level: TrustLevel = TrustLevel.OFFICIAL_MANUAL
    author: Optional[str] = None
    version: Optional[str] = None
    effective_date: Optional[str] = None
    page_count: Optional[int] = None
    summary: Optional[str] = None


class Provenance(BaseModel):
    document_id: str
    document_title: str
    file_type: str
    page: Optional[int] = None
    section: Optional[str] = None
    element_id: Optional[str] = None
    verbatim_quote: Optional[str] = None
    trust_level: TrustLevel = TrustLevel.OFFICIAL_MANUAL
    location_detail: Optional[str] = None


class VersionScope(BaseModel):
    min_software_version: Optional[str] = None
    max_software_version: Optional[str] = None
    applies_to_notes: Optional[str] = None


class Entity(BaseModel):
    id: str                                    # Canonical ID, e.g. "PS-04A"
    canonical_name: str
    aliases: List[str] = Field(default_factory=list)
    entity_type: EntityType = EntityType.COMPONENT
    location: Optional[str] = None
    status: str = "Active"                     # "Active", "Superseded", "Planned"
    system: str = "Aegis Series-7 HCS"
    notes: Optional[str] = None
    direct_connections: List[str] = Field(default_factory=list) # IDs connected to this entity


class Fact(BaseModel):
    id: str
    subject_id: str                            # Canonical entity ID
    predicate: str                             # E.g. "normal_operating_pressure", "location", "connected_to"
    object_value: Any                          # 200, "Hydraulic Module", True, etc.
    unit: Optional[str] = None                 # "bar", "seconds", "V", "mA"
    version_scope: Optional[VersionScope] = None
    trust_level: TrustLevel = TrustLevel.OFFICIAL_MANUAL
    confidence: float = 1.0
    status: FactStatus = FactStatus.ACTIVE
    provenance: Provenance
    notes: Optional[str] = None


class Conflict(BaseModel):
    id: str
    subject_id: str
    predicate: str
    conflicting_fact_ids: List[str]
    resolution_type: str                       # "TEMPORAL_SUPERSEDED", "TRUST_HIERARCHY", "DIFFERENT_SUBSYSTEM"
    resolved_fact_id: Optional[str] = None
    justification: str


class EpistemicGap(BaseModel):
    id: str
    target_topic: str
    missing_predicate: str
    explanation: str
    source_scanned: List[str] = Field(default_factory=list)


class Claim(BaseModel):
    statement: str
    supporting_fact_ids: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    verification_status: str = "VERIFIED"


class QueryResult(BaseModel):
    query_id: Optional[int] = None
    query: str
    epistemic_status: EpistemicStatus
    direct_answer: str
    claims: List[Claim] = Field(default_factory=list)
    evidence: List[Provenance] = Field(default_factory=list)
    conflicts_identified: List[Conflict] = Field(default_factory=list)
    gaps_identified: List[EpistemicGap] = Field(default_factory=list)
    confidence_score: float = 1.0


class KnowledgeStoreExport(BaseModel):
    system_name: str = "Aegis Series-7 HCS Knowledge Base"
    extraction_timestamp: str
    entities: Dict[str, Entity] = Field(default_factory=dict)
    facts: List[Fact] = Field(default_factory=list)
    conflicts: List[Conflict] = Field(default_factory=list)
    entity_alias_index: Dict[str, str] = Field(default_factory=dict) # lowercase alias -> canonical_id
