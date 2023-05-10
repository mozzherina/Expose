from typing import List

from expose.project.view import View
from expose.project import PACKAGE_TYPE, PROPERTY_TYPE, LITERAL_TYPE, \
    generate_id, ElementDict, BasicDict


class Element:
    def __init__(self, element: dict):
        self._id = element["id"]
        self._name = element["name"]
        self._type = element["type"]
        self._description = element["description"] if "description" in element else None
        self._views: List[View] = []  # all views on all the diagrams

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str):
        self._name = new_name

    @property
    def type(self) -> str:
        return self._type

    @property
    def views(self) -> List[View]:
        return self._views

    def to_json(self) -> dict:
        return {"id": self._id,
                "name": self._name,
                "description": self._description,
                "type": self._type}

    def add_view(self, view: View):
        self._views.append(view)

    def get_view(self, diagram_id) -> View | None:
        """
        Returns view on the given diagram
        :param diagram_id: id of the Diagram
        :return: View if found
        """
        for view in self._views:
            if view.diagram_id == diagram_id:
                return view
        return None

    def has_view(self, view_id: str) -> bool:
        """
        Check if the Element has View with the given id.
        N.B. This function is needed only because of the issue with
        possible inversion of Relations
        :param view_id: id of the View to be checked
        """
        for view in self._views:
            if view.id == view_id:
                return True
        return False

    def get_all_diagrams(self) -> set:
        """
        Returns all diagrams on which the Element can be found
        :return: set of diagrams' ids
        """
        diagrams = set()
        for view in self._views:
            diagrams.add(view.diagram_id)
        return diagrams


class Model(Element):
    def __init__(self, model: dict):
        super().__init__(model)
        self._property = model["propertyAssignments"]
        self._contents = self.get_all_packages(model["contents"])

    @staticmethod
    def get_all_packages(contents: List) -> List:
        result = []
        if contents:
            for element in contents:
                if element["type"] == PACKAGE_TYPE:
                    result.append(Model(element))
        return result

    def to_json(self) -> dict:
        result = super().to_json()
        result["propertyAssignments"] = self._property
        result["contents"] = [element.to_json() for element in self._contents]
        return result


class Diagram(Element):
    def __init__(self, diagram: dict):
        super().__init__(diagram)
        self._owner: BasicDict = diagram["owner"]
        self._elements: dict[str, View] = dict()  # id -> View

    def to_json(self) -> dict:
        result = super().to_json()
        result["owner"] = self._owner
        result["contents"] = [view.to_json() for view in self._elements.values()]
        return result

    @property
    def elements(self) -> dict[str, View]:
        return self._elements

    @elements.setter
    def elements(self, new_elements: dict):
        self._elements = new_elements

    def add_element(self, new_element: View):
        self._elements[new_element.id] = new_element

    def del_element(self, view_id: str) -> View:
        return self._elements.pop(view_id, None)


class Property(Element):
    def __init__(self, name: str, property_type: BasicDict = None, cardinality: str = None):
        super().__init__(ElementDict(
            id=generate_id(), name=name, type=PROPERTY_TYPE
        ))
        self._propertyType = property_type
        self._cardinality = cardinality

    def to_json(self) -> dict:
        result = super().to_json()
        result["propertyAssignments"] = None
        result["stereotype"] = None
        result["isDerived"] = False
        result["isReadOnly"] = True
        result["isOrdered"] = False
        result["cardinality"] = self._cardinality
        result["propertyType"] = self._propertyType
        result["subsettedProperties"] = None
        result["redefinedProperties"] = None
        result["aggregationKind"] = "NONE"
        return result


class Literal(Element):
    def __init__(self, name: str):
        super().__init__(ElementDict(
            id=generate_id(), name=name, type=LITERAL_TYPE
        ))

    def to_json(self) -> dict:
        result = super().to_json()
        result["propertyAssignments"] = None
        return result
