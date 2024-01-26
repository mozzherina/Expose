from expose import *
from expose.project import *
from expose.project.element import Element, Property


class Entity(Element):
    def __init__(self, entity: dict):
        """
        Complete initialization out of the dict
        :param entity: dict with all properties
        """
        super().__init__(entity)
        self._stereotype = entity["stereotype"]
        for key in ElementDict.__annotations__.keys():
            entity.pop(key, "")
        self._rest = entity

        # relation_type -> [id_relation]
        self._in_edges: RelationsDict = {PART_OF_TYPE: [], RELATION_TYPE: [], GENERAL_TYPE: []}
        self._out_edges: RelationsDict = {PART_OF_TYPE: [], RELATION_TYPE: [], GENERAL_TYPE: []}

    @classmethod
    def init_from_id(cls, _id: str):
        """
        Used for creating prototypes of entities
        ~ kind of promise to relations that Entity with this id exists
        :param _id: _id of the Entity
        """
        return cls(dict(id=_id, name="", type="", stereotype=""))

    def update(self, entity: dict):
        """
        Updates prototype to a normal Entity
        :param entity: dict with all properties
        """
        self._name = entity["name"]
        self._description = entity["description"]
        self._type = entity["type"]
        self._stereotype = entity["stereotype"]
        for key in ElementDict.__annotations__.keys():
            entity.pop(key, "")
        self._rest = entity

    def to_json(self) -> dict:
        result = super().to_json()
        result["stereotype"] = self._stereotype
        result.update(self._rest)
        return result

    def to_expo(self) -> dict:
        """
        Converts Entity to Expo format
        :return: dict with all properties
        """
        return {
            "id": self._id,
            "name": self._name,
            "fullName": f"{self._stereotype}:{self._name}" if self._stereotype else self._name,
            "color": self._set_colour(),
            "symbolType": self._set_symbol_type(),
            "x": self.views[0].get_x() if self.views else 0,
            "y": self.views[0].get_y() if self.views else 0
        }

    def _set_colour(self) -> str:
        """
        Sets colour for the Entity
        :return: colour in hex format
        """
        colour = GRAPH_BASIC_COLOUR

        if self._rest["restrictedTo"]:
            if self._rest["restrictedTo"][0] == "relator":
                colour = GRAPH_RELATOR_COLOUR
            elif self._rest["restrictedTo"][0] == "event":
                colour = GRAPH_EVENT_COLOUR
            elif self._rest["restrictedTo"][0] == "functional-complex":
                colour = GRAPH_OBJECT_COLOUR
            elif self._rest["restrictedTo"][0] == "intrinsic-mode":
                colour = GRAPH_MODE_COLOUR

        if self._stereotype == ClassStereotype.RELATOR.value:
            colour = GRAPH_RELATOR_COLOUR
        elif self._stereotype == ClassStereotype.QUALITY.value \
                or self._stereotype == ClassStereotype.MODE.value:
            colour = GRAPH_MODE_COLOUR
        elif self._stereotype == ClassStereotype.ENUMERATION.value \
                or self._stereotype == ClassStereotype.DATATYPE.value \
                or self._stereotype == ClassStereotype.ABSTRACT.value:
            colour = GRAPH_ENUMERATION_COLOUR
        elif self._stereotype == ClassStereotype.EVENT.value \
                or self._stereotype == ClassStereotype.SITUATION.value:
            colour = GRAPH_EVENT_COLOUR
        elif self._stereotype == ClassStereotype.KIND.value \
                or self._stereotype == ClassStereotype.CATEGORY.value \
                or self._stereotype == ClassStereotype.QUANTITY.value \
                or self._stereotype == ClassStereotype.COLLECTIVE.value:
            colour = GRAPH_OBJECT_COLOUR
        elif self._stereotype == ClassStereotype.ROLE.value \
                or self._stereotype == ClassStereotype.PHASE.value \
                or self._stereotype == ClassStereotype.SUBKIND.value:
            colour = color_variant(colour, GRAPH_COLOUR_VARIATION)
        else:
            colour = GRAPH_BASIC_COLOUR

        return colour

    def _set_symbol_type(self) -> str:
        """
        Sets colour for the Entity
        :return: colour in hex format
        """
        if self._stereotype == ClassStereotype.RELATOR.value:
            return GRAPH_RELATOR_SYMBOL
        elif self._stereotype == ClassStereotype.QUALITY.value \
                or self._stereotype == ClassStereotype.MODE.value:
            return GRAPH_MODE_SYMBOL
        elif self._stereotype == ClassStereotype.ENUMERATION.value \
                or self._stereotype == ClassStereotype.DATATYPE.value \
                or self._stereotype == ClassStereotype.ABSTRACT.value:
            return GRAPH_ENUMERATION_SYMBOL
        elif self._stereotype == ClassStereotype.EVENT.value \
                or self._stereotype == ClassStereotype.SITUATION.value:
            return GRAPH_EVENT_SYMBOL
        else:
            return GRAPH_BASIC_SYMBOL

    def __str__(self):
        if self.name:
            return self.name
        else:
            return ""

    @staticmethod
    def init_enumeration(literals: List, name: str = None) -> dict:
        """
        Initializes new enumeration from scratch
        :param literals: dict of Literals to be added to rest
        :param name: name of the future enumeration
        :return: prototype for Entity
        """
        return {
            "id": generate_id(),
            "name": name if name else "Enumeration_" + generate_id(2),
            "description": None,
            "type": CLASS_TYPE,
            "propertyAssignments": None,
            "stereotype": ClassStereotype.ENUMERATION.value,
            "isAbstract": False,
            "isDerived": False,
            "properties": None,
            "isExtensional": None,
            "isPowertype": None,
            "order": None,
            "literals": literals,
            "restrictedTo": [ClassStereotype.ABSTRACT]
        }

    @staticmethod
    def init_entity(name: str, stereotype: str) -> dict:
        """
        Initializes new entity from scratch
        :param name: name of the future entity
        :param stereotype: stereotype of the future entity
        :return: prototype for Entity
        """
        return {
            "id": generate_id(),
            "name": name,
            "description": None,
            "type": CLASS_TYPE,
            "propertyAssignments": None,
            "stereotype": stereotype,
            "isAbstract": False,
            "isDerived": False,
            "properties": None,
            "isExtensional": None,
            "isPowertype": None,
            "order": None,
            "literals": None,
            "restrictedTo": ["functional-complex"]
        }

    @property
    def stereotype(self) -> str:
        return self._stereotype

    @property
    def rest(self) -> dict:
        return self._rest

    @property
    def in_edges(self) -> RelationsDict:
        return self._in_edges

    @property
    def out_edges(self) -> RelationsDict:
        return self._out_edges

    def add_outgoing(self, relation_type: EdgeType, relation_id: str):
        """
        Adds id for the outgoing relation
        :param relation_type: PART_OF_TYPE | GENERAL_TYPE | RELATION_TYPE
        :param relation_id: id of the relation
        """
        self._out_edges[relation_type].append(relation_id)

    def del_outgoing(self, relation_type: EdgeType, relation_id: str):
        """
        Removes id of the outgoing relation
        :param relation_type: PART_OF_TYPE | GENERAL_TYPE | RELATION_TYPE
        :param relation_id: id of the relation
        """
        self._out_edges[relation_type].remove(relation_id)

    def add_incoming(self, relation_type: EdgeType, relation_id: str):
        """
        Adds id for the incoming relation
        :param relation_type: PART_OF_TYPE | GENERAL_TYPE | RELATION_TYPE
        :param relation_id: id of the relation
        """
        self._in_edges[relation_type].append(relation_id)

    def del_incoming(self, relation_type: EdgeType, relation_id: str):
        """
        Removes id of the incoming relation
        :param relation_type: PART_OF_TYPE | GENERAL_TYPE | RELATION_TYPE
        :param relation_id: id of the relation
        """
        self._in_edges[relation_type].remove(relation_id)

    def has_other_up_edges(self) -> bool:
        """
        Finds out if there are other up relations,
        that would require edges movement
        :return: True, if there are other relations
        """
        return len(self._out_edges["PartOf"] + self._out_edges["Generalization"]) > 1

    def get_in_edges(self, edge_type=None) -> List[str]:
        if edge_type:
            if edge_type in ["PartOf", "Relation", "Generalization"]:
                return self._in_edges[edge_type]
            else:
                return []
        else:
            return self._in_edges["PartOf"] \
                   + self._in_edges["Relation"] \
                   + self._in_edges["Generalization"]

    def get_out_edges(self, edge_type=None) -> List[str]:
        if edge_type:
            if edge_type in ["PartOf", "Relation", "Generalization"]:
                return self._out_edges[edge_type]
            else:
                return []
        else:
            return self._out_edges["PartOf"] \
                   + self._out_edges["Relation"] \
                   + self._out_edges["Generalization"]

    def get_all_edges(self) -> (List[str], List[str]):
        """
        Returns all relations of the Entity in
        two lists: all in relation ids, all out relation ids
        :return: [in_id], [out_id]
        """
        return self.get_in_edges(), self.get_out_edges()

    def get_number_of_edges(self) -> int:
        """
        Returns number of all relations for this Entity,
        used for Relators
        :return: number of edges for this Entity
        """
        return len(self.get_in_edges()) + len(self.get_out_edges())

    def add_attribute(self, attribute_name: str):
        """
        Adds new attribute to the Entity.
        Also modifies views
        :param attribute_name: name of the attribute
        """
        _property = Property(attribute_name).to_json()
        if self._rest["properties"]:
            self._rest["properties"] = self._rest["properties"] + [_property]
        else:
            self._rest["properties"] = [_property]

        for view in self._views:
            view.increase_shape_height(ATTRIBUTE_HEIGHT)
