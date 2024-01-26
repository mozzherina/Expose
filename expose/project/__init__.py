"""This package describes Graph structure."""
import random
import string

from enum import Enum
from typing import List, TypedDict, Final, Literal

from expose import ID_LENGTH


"""
------------------------------------------------------------
Constants for processing JSON
------------------------------------------------------------
"""
PACKAGE_TYPE: Final[str] = "Package"
PROPERTY_TYPE: Final[str] = "Property"
LITERAL_TYPE: Final[str] = "Literal"
CLASS_TYPE: Final[str] = "Class"
PART_OF_TYPE: Final[str] = "PartOf"
RELATION_TYPE: Final[str] = "Relation"
GENERAL_TYPE: Final[str] = "Generalization"
GEN_SET_TYPE: Final[str] = "GeneralizationSet"

CLASS_VIEW_TYPE: Final[str] = "ClassView"
RELATION_VIEW_TYPE: Final[str] = "RelationView"
GENERAL_VIEW_TYPE: Final[str] = "GeneralizationView"
GEN_SET_VIEW_TYPE: Final[str] = "GeneralizationSetView"

EdgeType = Literal["PartOf", "Generalization", "Relation"]


"""
------------------------------------------------------------
Typed dictionaries
------------------------------------------------------------
"""


class BasicDict(TypedDict):
    id: str
    type: str


class ElementDict(BasicDict, total=False):
    name: str
    description: str
    stereotype: str


class PointDict(TypedDict):
    x: int
    y: int


class ShapeDict(BasicDict, total=False):
    x: int  # for ClassView, GeneralizationSetView
    y: int  # for ClassView, GeneralizationSetView
    width: int  # for ClassView, GeneralizationSetView
    height: int  # for ClassView, GeneralizationSetView
    points: List[PointDict]  # for RelationView, GeneralizationView
    value: str  # for GeneralizationSetView


class RelationsDict(TypedDict):
    PartOf: List
    Relation: List
    Generalization: List


"""
------------------------------------------------------------
Structure for work with stereotypes
------------------------------------------------------------
"""


class ClassStereotype(Enum):
    TYPE: Final[str] = "type"
    HISTORICAL_ROLE: Final[str] = "historicalRole"
    HISTORICAL_ROLE_MIXIN: Final[str] = "historicalRoleMixin"
    EVENT: Final[str] = "event"
    SITUATION: Final[str] = "situation"
    CATEGORY: Final[str] = "category"
    MIXIN: Final[str] = "mixin"
    ROLE_MIXIN: Final[str] = "roleMixin"
    PHASE_MIXIN: Final[str] = "phaseMixin"
    KIND: Final[str] = "kind"
    COLLECTIVE: Final[str] = "collective"
    QUANTITY: Final[str] = "quantity"
    RELATOR: Final[str] = "relator"
    QUALITY: Final[str] = "quality"
    MODE: Final[str] = "mode"
    SUBKIND: Final[str] = "subkind"
    ROLE: Final[str] = "role"
    PHASE: Final[str] = "phase"
    ENUMERATION: Final[str] = "enumeration"
    DATATYPE: Final[str] = "datatype"
    ABSTRACT: Final[str] = "abstract"


class RelationStereotype(Enum):
    MATERIAL: Final[str] = "material"
    DERIVATION: Final[str] = "derivation"
    COMPARATIVE: Final[str] = "comparative"
    MEDIATION: Final[str] = "mediation"
    CHARACTERIZATION: Final[str] = "characterization"
    EXTERNAL_DEPENDENCE: Final[str] = "externalDependence"
    COMPONENT_OF: Final[str] = "componentOf"
    MEMBER_OF: Final[str] = "memberOf"
    SUBCOLLECTION_OF: Final[str] = "subCollectionOf"
    SUBQUANTITY_OF: Final[str] = "subQuantityOf"
    INSTANTIATION: Final[str] = "instantiation"
    TERMINATION: Final[str] = "termination"
    PARTICIPATIONAL: Final[str] = "participational"
    PARTICIPATION: Final[str] = "participation"
    HISTORICAL_DEPENDENCE: Final[str] = "historicalDependence"
    CREATION: Final[str] = "creation"
    MANIFESTATION: Final[str] = "manifestation"
    BRINGS_ABOUT: Final[str] = "bringsAbout"
    TRIGGERS: Final[str] = "triggers"


NON_SORTAL_STEREOTYPES = [
    ClassStereotype.CATEGORY.value,
    ClassStereotype.MIXIN.value,
    ClassStereotype.PHASE_MIXIN.value,
    ClassStereotype.ROLE_MIXIN.value,
    ClassStereotype.HISTORICAL_ROLE_MIXIN.value
]

SORTAL_STEREOTYPES = [
    ClassStereotype.KIND.value,
    ClassStereotype.COLLECTIVE.value,
    ClassStereotype.QUANTITY.value,
    ClassStereotype.RELATOR.value,
    ClassStereotype.QUALITY.value,
    ClassStereotype.MODE.value,
    ClassStereotype.SUBKIND.value,
    ClassStereotype.PHASE.value,
    ClassStereotype.ROLE.value,
    ClassStereotype.HISTORICAL_ROLE.value
]

KINDS_STEREOTYPES = [
    ClassStereotype.KIND.value,
    ClassStereotype.COLLECTIVE.value,
    ClassStereotype.QUANTITY.value,
    ClassStereotype.RELATOR.value,
    ClassStereotype.QUALITY.value,
    ClassStereotype.MODE.value
]

ASPECTS = [
    ClassStereotype.RELATOR.value,
    ClassStereotype.QUALITY.value,
    ClassStereotype.MODE.value
]

ENDURANT_OR_DATATYPE = SORTAL_STEREOTYPES + \
                       NON_SORTAL_STEREOTYPES + \
                       [ClassStereotype.DATATYPE.value]

NOT_OBJECTS = ASPECTS + [ClassStereotype.EVENT.value]


"""
------------------------------------------------------------
ID generation function
------------------------------------------------------------
"""


def generate_id(length: int = ID_LENGTH) -> str:
    """
    Generates ids for new Elements
    """
    return "".join([random.choice(string.ascii_letters + string.digits) for _ in range(length)])


def color_variant(hex_color, brightness_offset=1) -> str:
    rgb_hex = [hex_color[x:x+2] for x in [1, 3, 5]]
    new_rgb_int = [int(hex_value, 16) + brightness_offset for hex_value in rgb_hex]
    new_rgb_int = [min([255, max([0, i])]) for i in new_rgb_int]
    return "#" + "".join([hex(i)[2:] for i in new_rgb_int]).upper()
