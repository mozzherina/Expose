import expose
import copy

from expose.project import *
from expose import DEFAULT_X, DEFAULT_Y, DEFAULT_WIDTH, \
    DEFAULT_HEIGHT, ATTRIBUTE_HEIGHT


class View:
    def __init__(self, element_view: dict, diagram_id: str):
        self._id = element_view["id"]
        self._type = element_view["type"]
        self._element: BasicDict = element_view["modelElement"]
        self._shape: ShapeDict = element_view["shape"]
        self._diagram_id = diagram_id

        # for Relations and Generalizations only
        if self._type in (RELATION_VIEW_TYPE, GENERAL_VIEW_TYPE):
            self._source: BasicDict = element_view["source"]
            self._target: BasicDict = element_view["target"]

    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, _id: str):
        self._id = _id

    @property
    def type(self) -> str:
        return self._type

    @property
    def diagram_id(self) -> str:
        return self._diagram_id

    @property
    def shape(self) -> ShapeDict:
        return self._shape

    @shape.setter
    def shape(self, new_shape: ShapeDict):
        self._shape = new_shape

    @property
    def element(self) -> BasicDict:
        return self._element

    @element.setter
    def element(self, new_element: BasicDict):
        self._element = new_element

    @property
    def source(self) -> BasicDict:
        return self._source

    @source.setter
    def source(self, new_source: BasicDict):
        self._source = new_source

    @property
    def target(self) -> BasicDict:
        return self._target

    @target.setter
    def target(self, new_target: BasicDict):
        self._target = new_target

    def get_x(self) -> int:
        if self._type == CLASS_VIEW_TYPE:
            return self._shape["x"]
        elif (self._type == RELATION_VIEW_TYPE) or (self._type == GENERAL_VIEW_TYPE):
            return self._shape["points"][0]["x"]
        else:
            return expose.DEFAULT_X

    def get_y(self) -> int:
        if self._type == CLASS_VIEW_TYPE:
            return self._shape["y"]
        elif (self._type == RELATION_VIEW_TYPE) or (self._type == GENERAL_VIEW_TYPE):
            return self._shape["points"][0]["y"]
        else:
            return expose.DEFAULT_Y

    def to_json(self) -> dict:
        result = {
            "id": self._id,
            "type": self._type,
            "modelElement": self._element,
            "shape": self._shape,
        }

        if self._type in (RELATION_VIEW_TYPE, GENERAL_VIEW_TYPE):
            result["source"] = self._source
            result["target"] = self._target
        return result

    def update_model_element_id(self, new_id: str):
        self._element["id"] = new_id

    def _make_edge_visible(self):
        if (len(self._shape["points"]) == 2) and \
                (str(self._shape["points"][0].values()) == str(self._shape["points"][-1].values())):
            fst = copy.copy(self._shape["points"][0])
            snd = copy.copy(self._shape["points"][0])
            trd = copy.copy(self._shape["points"][0])
            fst["x"] += DEFAULT_WIDTH
            snd["x"] += DEFAULT_WIDTH
            snd["y"] += DEFAULT_HEIGHT
            trd["y"] += DEFAULT_HEIGHT
            self._shape["points"] = [self._shape["points"][0]] + [fst, snd, trd] + [self._shape["points"][-1]]

    def update_source_point(self, new_point: PointDict):
        # TODO: make this function more advanced
        self._shape["points"] = [new_point] + self._shape["points"][1:]
        self._make_edge_visible()

    def update_target_point(self, new_point: PointDict):
        # TODO: make this function more advanced
        self._shape["points"] = self._shape["points"][:-1] + [new_point]
        self._make_edge_visible()

    def increase_shape_height(self, value: int = ATTRIBUTE_HEIGHT):
        if self._type == CLASS_VIEW_TYPE:
            self._shape["height"] = self._shape["height"] + value

    def get_center(self) -> PointDict:
        """
        Returns center of the rectangle, that represents Entity
        :return: PointDict with x, y
        """
        return PointDict(
            x=self._shape["x"] + self._shape["width"] // 2,
            y=self._shape["y"] + self._shape["height"] // 2
        )

    @classmethod
    def create_entity_view(cls, element_id: str, diagram_id: str,
                           x: int = DEFAULT_X, y: int = DEFAULT_Y,
                           width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT):
        """
        Create view for an Entity from scratch.
        N.B. Does NOT add view to the diagram
        :param element_id: modelElement id
        :param diagram_id: diagram in which the view is associated with
        :param x: Shape.x
        :param y: Shape.y
        :param width: Shape.width
        :param height: Shape.height
        """
        _id = generate_id()
        element = BasicDict(id=element_id, type=CLASS_TYPE)
        shape = ShapeDict(id=_id + "_shape", type="Rectangle",
                          x=x, y=y, width=width, height=height)
        view = dict(id=_id, type=CLASS_VIEW_TYPE, modelElement=element, shape=shape)
        # TODO: not working
        # expose.DEFAULT_Y += height + ATTRIBUTE_HEIGHT  # for future entities
        return cls(view, diagram_id)

    @classmethod
    def create_edge_view(cls, is_relation: bool, element_id: str, source_view_id: str,
                         target_view_id: str, diagram_id: str, points: List[PointDict]):
        """
        Create view for a Relation/Generalization from scratch.
        N.B. Does NOT add view to the diagram
        :param is_relation: True if Relation, False if Generalization
        :param element_id: modelElement id
        :param source_view_id: Source.id
        :param target_view_id: Target.id
        :param diagram_id: diagram in which the view is associated with
        :param points: List of PointDict for creating a Path
        """
        _id = generate_id()
        element = BasicDict(id=element_id, type=RELATION_TYPE if is_relation else GENERAL_TYPE)
        shape = ShapeDict(id=_id + "_shape", type="Path", points=points)
        # The following is needed because of VisualParadigm policy
        source = BasicDict(id=source_view_id if is_relation else target_view_id, type=CLASS_VIEW_TYPE)
        target = BasicDict(id=target_view_id if is_relation else source_view_id, type=CLASS_VIEW_TYPE)
        # end of patch
        view = dict(id=_id, type=RELATION_VIEW_TYPE if is_relation else GENERAL_VIEW_TYPE,
                    modelElement=element, shape=shape, source=source, target=target)
        return cls(view, diagram_id)

    @classmethod
    def create_set_view(cls, element_id: str, diagram_id: str, x: int, y: int):
        """
        Create view for a GeneralizationSet from scratch.
        N.B. Does NOT add view to the diagram
        :param element_id: generalization set id
        :param diagram_id: diagram in which the view is associated with
        :param x: x position
        :param y: y position
        """
        _id = generate_id()
        element = BasicDict(id=element_id, type=GEN_SET_TYPE)
        shape = ShapeDict(id=_id + "_shape", type="Text", x=x, y=y, width=50, height=15, value="")
        view = dict(id=_id, type=GEN_SET_VIEW_TYPE, modelElement=element, shape=shape)
        return cls(view, diagram_id)

    def invert(self):
        """
        Exchange source and target of RelationView.
        N.B. This function is needed only because of the issue with
        possible inversion of Relations
        """
        self._source, self._target = self._target, self._source
        self._shape["points"].reverse()
