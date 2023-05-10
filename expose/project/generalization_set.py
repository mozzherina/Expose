from typing import List

from expose.project import GENERAL_TYPE, GEN_SET_TYPE, ElementDict, BasicDict, generate_id
from expose.project.element import Element
from expose.project.relation import Generalization


class GeneralizationSet(Element):
    def __init__(self, entity: dict, generalizations: List[Generalization], names: dict):
        """
        Creates GeneralizationSet object
        :param entity: Dict of all information about GeneralizationSet
        :param generalizations: List of Generalizations
        :param names: Dict of names of additional classes names
        """
        super().__init__(entity)
        self._generalizations = generalizations
        entity.pop("generalizations")
        for key in ElementDict.__annotations__.keys():
            entity.pop(key, "")

        # processing "categorizer" attribute
        if entity["categorizer"] is not None:
            if entity["categorizer"]["id"] in names:
                self.name = names[entity["categorizer"]["id"]]
            entity["categorizer"] = None
        self._rest = entity

    @classmethod
    def get_ids(cls, element: dict) -> List[str]:
        """
        Returns list of Generalizations' ids from this GeneralizationSet
        :param element: Dict of all information about GeneralizationSet
        :return: List of Generalizations' ids
        """
        result = []
        # Added because of "sportbooking2021" or "spo2017" model
        if ("generalizations" not in element) or (element["generalizations"] is None):
            return result
        for key in element["generalizations"]:
            result.append(key["id"])
        return result

    @property
    def generalizations(self) -> List[Generalization]:
        return self._generalizations

    @property
    def rest(self) -> dict:
        return self._rest

    def to_json(self) -> dict:
        result = super().to_json()
        result.update(self._rest)
        result["generalizations"] = [BasicDict(id=g.id, type=GENERAL_TYPE) for g in self._generalizations]
        return result

    def to_expo(self) -> str:
        """
        Converts GeneralizationSet to readable format
        :return: String with all properties
        """
        result = GEN_SET_TYPE + " ("
        result += "complete, " if self._rest["isComplete"] else "not complete, "
        result += "disjoint" if self._rest["isDisjoint"] else "not disjoint"
        result += "): {"
        for key in self._generalizations:
            result += f"{key.from_entity.name} -> {key.to_entity.name}, "
        result = result[:-2] + "}"
        return result

    def __str__(self):
        result = GEN_SET_TYPE + " {"
        result += "c," if self._rest["isComplete"] else "nc,"
        result += "d" if self._rest["isDisjoint"] else "nd"
        result += "}:"
        for key in self._generalizations:
            result += f" {key.id},"
        return result[:-1]

    @staticmethod
    def init_generalization_set(generalizations: List[Generalization], complete: bool, disjoint: bool) -> dict:
        """
        Initializes new GeneralizationSet from scratch
        :param generalizations: List of Generalizations
        :param complete: Is GeneralizationSet complete
        :param disjoint: Is GeneralizationSet disjoint
        :return: prototype for GeneralizationSet
        """
        genset = {
            "id": generate_id(),
            "name": "GS",
            "description": None,
            "type": GEN_SET_TYPE,
            "propertyAssignments": None,
            "isDisjoint": disjoint,
            "isComplete": complete,
            "categorizer": None,
            "generalizations": []
        }
        for generalization in generalizations:
            genset["generalizations"].append(BasicDict(id=generalization.id, type=GENERAL_TYPE))
        return genset

    def is_complete_and_disjoint(self) -> bool:
        return self._rest["isComplete"] and self._rest["isDisjoint"]

    def is_complete(self) -> bool:
        return self._rest["isComplete"]

    def is_disjoint(self) -> bool:
        return self._rest["isDisjoint"]

    def del_generalization(self, generalization: Generalization):
        if self._rest["isComplete"]:
            self._rest["isComplete"] = False
        self._generalizations.remove(generalization)
