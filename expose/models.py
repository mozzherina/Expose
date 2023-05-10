from pydantic import BaseModel
from typing import List
from expose import EXPAND_MAX_NUMBER, LONG_NAMES, MULT_RELATIONS, KEEP_RELATORS


class GraphModel(BaseModel):
    origin: dict
    in_format: str
    out_format: str
    height: int = 0
    width: int = 0


class BasicModel(GraphModel):
    node: str


class ExpandModel(BasicModel):
    limit: int = EXPAND_MAX_NUMBER


class FocusModel(BasicModel):
    hop: int


class DeleteModel(GraphModel):
    element_id: str
    element_type: str = "node"  # "link"


class FoldModel(BasicModel):
    long_names: bool = LONG_NAMES
    mult_relations: bool = MULT_RELATIONS


class AbstractModel(GraphModel):
    abs_type: List[str]
    long_names: bool = LONG_NAMES
    mult_relations: bool = MULT_RELATIONS
    keep_relators: bool = KEEP_RELATORS
