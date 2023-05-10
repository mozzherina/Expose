from abc import ABC, abstractmethod

from expose import GRAPH_STROKE_WIDTH, GRAPH_STROKE_DASHARRAY
from expose.project import *
from expose.project.element import Element, Property
from expose.project.entity import Entity


class AbcRelation(ABC, Element):
    def __init__(self, entity: dict, entity_from: Entity, entity_to: Entity):
        super().__init__(entity)
        self._final_type = self._type
        self._from = entity_from
        self._to = entity_to

    @classmethod
    @abstractmethod
    def get_ids(cls, element: dict) -> (str, str):
        """
        Hides getting ids from the json dict
        :param element: json list of all content
        :return: (id_from, id_to)
        """
        pass

    @abstractmethod
    def __str__(self):
        pass

    def to_json(self) -> dict:
        result = super().to_json()
        return result

    @abstractmethod
    def to_expo(self) -> dict:
        pass

    @property
    def from_entity(self) -> Entity:
        return self._from

    @property
    def to_entity(self) -> Entity:
        return self._to

    @property
    def type(self) -> EdgeType:
        return self._final_type

    @abstractmethod
    def update_ids(self, diagrams: dict) -> str:
        """
        Updates all ids that are inside the relation
        so there would be no duplicates in the whole schema
        :param diagrams: Dict of all Diagrams
        :return: new id of the relation
        """
        pass

    def update_views(self, diagrams: dict):
        """
        Updates all Views' ids that are inside the relation
        so there would be no duplicates in the whole schema.
        Also adds new views to the Diagrams
        :param diagrams: Dict of all Diagrams
        """
        for (i, view) in enumerate(self.views):
            view.id = f"{self._id}_view_{i}"
            view.element["id"] = self._id
            view.shape["id"] = view.id + "_path"
            diagrams[view.diagram_id].add_element(view)

    def _update_end(self, is_source: bool, new_entity: Entity) -> List:
        """
        Called from move, update views according to new_entity
        :param is_source: True, if moving from-end
        :param new_entity: link to new Entity as new end
        :return: views that should be deleted from diagrams, [(diagram_id, view_id)]
        """
        unnecessary_views = []
        for view in self.views:
            diagram_id = view.diagram_id
            if new_entity.get_view(diagram_id):
                entity_center = new_entity.get_view(diagram_id).get_center()
                if is_source:
                    view.update_source_point(entity_center)
                    view.source["id"] = new_entity.get_view(diagram_id).id
                else:
                    view.update_target_point(entity_center)
                    view.target["id"] = new_entity.get_view(diagram_id).id
            else:
                # there is no corresponding view in this diagram
                unnecessary_views.append((diagram_id, view.id))
        return unnecessary_views

    def move(self, new_from: Entity, new_to: Entity, diagrams: dict):
        """
        Moves to the new_from and/or new_to Entity
        :param new_from: new from Entity
        :param new_to: new to Entity
        :param diagrams: dict of all Diagrams
        """
        views_to_delete = []
        if new_from:
            self._from = new_from
            views_to_delete += self._update_end(True, new_from)
        if new_to:
            self._to = new_to
            views_to_delete += self._update_end(False, new_to)

        for diagram_id, view_id in views_to_delete:
            diagrams[diagram_id].del_element(view_id)


class Generalization(AbcRelation):
    def __init__(self, entity: dict, entity_from: Entity, entity_to: Entity):
        super().__init__(entity, entity_from, entity_to)
        self._property = entity["propertyAssignments"] if "propertyAssignments" in entity else None
        self._set = None  # ids of generalization_set

    @classmethod
    def get_ids(cls, element: dict) -> (str, str):
        """
        N.B.: Here we ignore all Generalizations between Relations
        Test: GeneralizationRelation
        """
        if (element["specific"]["type"] == CLASS_TYPE) and \
                (element["general"]["type"] == CLASS_TYPE):
            return element["specific"]["id"], element["general"]["id"]
        else:
            return None, None

    @classmethod
    def init_from_id(cls, _id: str):
        """
        Used for creating prototypes of generalization
        ~ kind of promise to generalization sets that generalization with this id exists
        :param _id: _id of the Generalization
        """
        return cls(dict(id=_id, name="", type=GENERAL_TYPE), None, None)

    def update(self, entity: dict, entity_from: Entity, entity_to: Entity):
        """
        Updates prototype to a normal Generalization
        :param entity: dict with all properties
        :param entity_from: link to more specific Entity
        :param entity_to: link to more general Entity
        """
        self._name = entity["name"]
        self._description = entity["description"]
        self._type = entity["type"]
        self._property = entity["propertyAssignments"]
        self._from = entity_from
        self._to = entity_to

    @property
    def set(self) -> str:
        return self._set

    def add_to_set(self, set_id: str):
        self._set = set_id

    def remove_from_set(self):
        self._set = None

    def to_json(self) -> dict:
        result = super().to_json()
        result["propertyAssignments"] = self._property
        result["general"] = BasicDict(id=self.to_entity.id, type=self.to_entity.type)
        result["specific"] = BasicDict(id=self.from_entity.id, type=self.from_entity.type)
        return result

    def to_expo(self) -> dict:
        return {
            "id": self._id,
            "name": "",
            "source": self.from_entity.id,
            "target": self.to_entity.id,
            # TODO: check if different strokes are better
            # "strokeWidth": GRAPH_STROKE_WIDTH
            "strokeDasharray": GRAPH_STROKE_WIDTH
        }

    def __str__(self):
        if self._set:
            return f"generalization (also in set)"
        else:
            return "generalization"

    @staticmethod
    def init_generalization(specific_id: str, general_id: str) -> dict:
        """
        Initializes new Generalization from scratch
        :param specific_id: id of the source Entity
        :param general_id: id of the target Entity
        :return: prototype for Relation
        """
        _id = generate_id()
        relation = {
            "id": _id,
            "name": None,
            "description": None,
            "type": GENERAL_TYPE,
            "propertyAssignments": None,
            "general": { "id": general_id, "type": CLASS_TYPE },
            "specific": { "id": specific_id, "type": CLASS_TYPE }
        }
        return relation

    def update_ids(self, diagrams: dict) -> str:
        self._id = generate_id()
        super().update_views(diagrams)
        return self._id

    def move(self, new_from: Entity, new_to: Entity, diagrams: dict,
             new_name: str = None, role_from: str = None, role_to: str = None):
        """
        Moves to the new_from and/or new_to Entity
        :param new_from: new from Entity
        :param new_to: new to Entity
        :param diagrams: dict of all Diagrams
        :param new_name: ignored
        :param role_from: ignored
        :param role_to: ignored
        """
        super().move(new_from, new_to, diagrams)


class Relation(AbcRelation):
    def __init__(self, entity: dict, entity_from: Entity, entity_to: Entity):
        super().__init__(entity, entity_from, entity_to)
        self._stereotype = entity["stereotype"]
        for key in ElementDict.__annotations__.keys():
            entity.pop(key, "")
        self._rest = entity

        if not ((self.rest["properties"][0]["aggregationKind"] == "NONE") &
                (self.rest["properties"][1]["aggregationKind"] == "NONE")):
            self._final_type = PART_OF_TYPE

    @classmethod
    def get_ids(cls, element: dict) -> (str, str):
        if (not element["properties"][0]["propertyType"]) or (not element["properties"][1]["propertyType"]) \
                or (element["properties"][0]["propertyType"]["type"] != CLASS_TYPE) \
                or (element["properties"][1]["propertyType"]["type"] != CLASS_TYPE):
            return None, None
        return element["properties"][0]["propertyType"]["id"], element["properties"][1]["propertyType"]["id"]

    @property
    def stereotype(self) -> str:
        return self._stereotype

    @stereotype.setter
    def stereotype(self, new_stereotype: str):
        self._stereotype = new_stereotype

    @property
    def rest(self) -> dict:
        return self._rest

    @property
    def role_from(self) -> str:
        return self._rest["properties"][0]["name"]

    def clear_role_from(self):
        self._rest["properties"][0]["name"] = ""

    @property
    def role_to(self) -> str:
        return self._rest["properties"][1]["name"]

    def clear_role_to(self):
        self._rest["properties"][1]["name"] = ""

    def get_cardinality_from(self) -> str:
        return self._rest["properties"][0]["cardinality"]

    def get_cardinality_to(self) -> str:
        return self._rest["properties"][1]["cardinality"]

    @staticmethod
    def _relax_cardinality(original: str) -> str:
        """
        Relaxes lower bound of the cardinality constraints
        """
        if original == '*':
            return None  # it does not make much sense to have '*' as cardinality
        cardinality = original.split("..")
        if len(cardinality) > 1:
            if cardinality[1] == "*":
                return None  # it does not make much sense to have '*' as cardinality
            return "0.." + cardinality[1]
        else:  # options "1", "2", etc
            try:
                higher_bound = int(original)
                if higher_bound > 0:
                    return "0.." + str(higher_bound)
                else:
                    return None  # it does not make much sense to have '*' as cardinality
            except ValueError:
                return original  # not able to process

    def relax_cardinality_from(self):
        if self._rest["properties"][0]["cardinality"]:  # if cardinality is given
            self._rest["properties"][0]["cardinality"] = \
                Relation._relax_cardinality(self._rest["properties"][0]["cardinality"])

    def relax_cardinality_to(self):
        if self._rest["properties"][1]["cardinality"]:  # if cardinality is given
            self._rest["properties"][1]["cardinality"] = \
                Relation._relax_cardinality(self._rest["properties"][1]["cardinality"])

    @staticmethod
    def _minimal_cardinality(fst: str, snd: str) -> str:
        """
        Returns the broadest cardinality of two given
        """
        if fst == "*" or snd == "*":
            return None  # it does not make much sense to have '*' as cardinality

        fst_cardinality = fst.split("..")
        if len(fst_cardinality) < 2:
            fst_cardinality.append(fst_cardinality[0])
        snd_cardinality = snd.split("..")
        if len(snd_cardinality) < 2:
            snd_cardinality.append(snd_cardinality[0])

        try:
            lower_bound = min(int(fst_cardinality[0]), int(snd_cardinality[0]))
            if (fst_cardinality[1] == "*") or (snd_cardinality[1] == "*"):
                high_bound = "*"
                if lower_bound == 0:
                    return None  # it does not make much sense to have '0..*' as cardinality
            else:
                high_bound = str(max(int(fst_cardinality[1]), int(snd_cardinality[1])))
            if str(lower_bound) == high_bound:
                return high_bound
            return str(lower_bound) + ".." + high_bound
        except ValueError:
            return fst  # not able to process

    def set_minimal_cardinality_from(self, other_cardinality: str):
        if self._rest["properties"][0]["cardinality"] and other_cardinality:
            self._rest["properties"][0]["cardinality"] = self._minimal_cardinality(
                self._rest["properties"][0]["cardinality"], other_cardinality)
        else:
            self._rest["properties"][0]["cardinality"] = None

    def set_minimal_cardinality_to(self, other_cardinality: str):
        if self._rest["properties"][1]["cardinality"] and other_cardinality:
            self._rest["properties"][1]["cardinality"] = self._minimal_cardinality(
                self._rest["properties"][1]["cardinality"], other_cardinality)
        else:
            self._rest["properties"][1]["cardinality"] = None

    def to_json(self) -> dict:
        result = super().to_json()
        result["stereotype"] = self._stereotype
        result.update(self._rest)
        result["properties"][0]["propertyType"]["id"] = self.from_entity.id
        result["properties"][1]["propertyType"]["id"] = self.to_entity.id
        return result

    def to_expo(self) -> dict:
        """
        Converts Relation to Expo format
        :return: dict with all properties
        """
        full_name = ""
        if self._stereotype and self._name:
            full_name = f"{self._stereotype}:{self._name}"
        elif self._stereotype:
            full_name = self._stereotype
        elif self._name:
            full_name = self._name

        result = {
            "id": self._id,
            "name": self._name if self._name else full_name,
            "fullName": full_name,
            "source": self.from_entity.id,
            "target": self.to_entity.id
        }
        if self._final_type == PART_OF_TYPE:
            result["strokeDasharray"] = GRAPH_STROKE_WIDTH

        return result

    def __str__(self):
        return f"{self.stereotype}: {self.name}" if self.name else f"{self.stereotype}"

    def is_essential(self) -> bool:
        return self._rest["properties"][0]["isReadOnly"] and \
               self._rest["properties"][1]["isReadOnly"]

    def update_ids(self, diagrams: dict) -> str:
        self._id = generate_id()
        self.rest["properties"][0]["id"] = self._id + "_p0"
        self.rest["properties"][1]["id"] = self._id + "_p1"
        super().update_views(diagrams)
        return self._id

    def move(self, new_from: Entity, new_to: Entity, diagrams: dict,
             new_name: str = None, role_from: str = None, role_to: str = None):
        """
        Moves to the new_from and/or new_to Entity
        :param new_from: new from Entity
        :param new_to: new to Entity
        :param diagrams: dict of all Diagrams
        :param new_name: new relation name, if given
        :param role_from: new role name for from-end, if given
        :param role_to: new role name for to-end, if given
        """
        super().move(new_from, new_to, diagrams)
        if new_name is not None:
            self._name = new_name
        if role_from is not None:
            self._rest["properties"][0]["name"] = role_from
        if role_to is not None:
            self._rest["properties"][1]["name"] = role_to

    @staticmethod
    def init_relation(source_id: str, target_id: str, name: str = None,
                      cardinality_from: str = None, cardinality_to: str = None) -> dict:
        """
        Initializes new Relation from scratch
        :param source_id: id of the source Entity
        :param target_id: id of the target Entity
        :param name: optional name of the Relation
        :param cardinality_from: cardinality for the 'from' end
        :param cardinality_to: cardinality for the 'to' end
        :return: prototype for Relation
        """
        _id = generate_id()
        relation = {
            "id": _id,
            "name": name,
            "description": None,
            "type": RELATION_TYPE,
            "propertyAssignments": None,
            "stereotype": None,
            "isAbstract": False,
            "isDerived": False,
            "properties": [Property("", BasicDict(id=source_id, type=CLASS_TYPE),
                                    cardinality=cardinality_from).to_json(),
                           Property("", BasicDict(id=target_id, type=CLASS_TYPE),
                                    cardinality=cardinality_to).to_json()]
        }
        return relation

    def invert(self):
        """
        Exchange source and target of PartOf Relation.
        N.B. This function is needed only because of the issue with
        inversion of PartOf Relations
        """
        self._from, self._to = self._to, self._from
        self.rest["properties"][0], self.rest["properties"][1] = \
            self.rest["properties"][1], self.rest["properties"][0]

    def is_aggregation_from(self):
        """
        Check if aggregation is in the wrong (source) end
        N.B. This function is needed only because of the issue with
        inversion of PartOf Relations
        """
        return self.rest["properties"][0]["aggregationKind"] and (
                self.rest["properties"][0]["aggregationKind"] != "NONE")
