import copy
import logging

from expose import *
from expose.graph import BaseGraph
from expose.project import *
from expose.project.element import Element, Model, Diagram, Literal
from expose.project.entity import Entity
from expose.project.relation import Generalization, Relation
from expose.project.generalization_set import GeneralizationSet
from expose.project.view import View


class JSONGraph(BaseGraph, Element):
    def __init__(self, project: dict, verbalize: bool = True):
        self._verbalize = verbalize
        self.logger = logging.getLogger(LOG_NAME)
        if self._verbalize:
            self.logger.debug("Initialising graph of the model...")

        Element.__init__(self, project)
        self._entities: dict[str, List[Entity]] = {}  # stereotype -> [Entity]
        self._entity_ids: dict[str, Entity] = {}  # id -> Entity
        self._relations: RelationsDict = {PART_OF_TYPE: [], RELATION_TYPE: [], GENERAL_TYPE: []}
        self._relation_ids: dict[str, Relation | Generalization] = {}  # id -> Relation
        self._generalization_set_ids: dict[str, GeneralizationSet] = {}  # id -> GeneralizationSet
        self._diagrams: dict[str, Diagram] = {}  # id -> Diagram
        self._additional_entities: dict[str, Diagram] = {}  # id -> Name

        self._stack = []
        self._ids_to_be_abstracted = []

        # creating graph of all elements in the model
        self._model = Model(project["model"])  # create Model with all Packages in it
        all_contents = self.get_all_elements(project["model"]["contents"])  # get all Elements as list
        if all_contents:
            for element in all_contents:
                if element["type"] == CLASS_TYPE:
                    self.add_entity(element)
                elif element["type"] == GEN_SET_TYPE:
                    self.add_generalization_set(element)
                else:
                    self.add_relation(element)

        # creating all diagrams and adding views to the elements
        if project["diagrams"]:
            for diagram in project["diagrams"]:
                d = Diagram(diagram)
                if diagram["contents"]:
                    views = {}
                    for view in diagram["contents"]:
                        v = View(view, d.id)
                        if self.attach_view(v):  # add View to the corresponding element
                            views[v.id] = v  # if was successfully added, then also add to the Diagram
                    d.elements = views  # save all those Views in the Diagram
                self._diagrams[d.id] = d

        # TODO: debug this part taking into account log messages
        for diagram in self._diagrams.values():
            for view in diagram.elements.values():
                if view.type == RELATION_VIEW_TYPE:
                    # N.B.: additional check for a proper View
                    # because of possible 'inversion' of relations
                    # Test: GeneralizationSet, MemberPart
                    relation = self._relation_ids[view.element["id"]]
                    source = relation.from_entity
                    target = relation.to_entity
                    source_view = view.source["id"]
                    target_view = view.target["id"]
                    if not (source.has_view(source_view) and target.has_view(target_view)):
                        if source.has_view(target_view) and target.has_view(source_view):
                            if self._verbalize:
                                self.logger.warning(f"Inverted view of {relation.id} with stereotype {relation.stereotype}")
                            view.invert()
                        else:
                            self.logger.error(f"Check inversion of relation {relation.id}")

    def _add_to_stack(self, name: str) -> bool:
        """
        Check if there is a possibility of recursion
        :param name: name of the Entity for the abstraction
        :return: True if was not processed before
        """
        if name not in self._stack:
            self._stack.append(name)
            return True
        return False

    """
    ------------------------------------------------------------
    Graph building functions
    ------------------------------------------------------------
    """

    def get_all_elements(self, contents: dict) -> List:
        """
        Forms a list of all model elements (entities, relations),
        Packages themselves are ignored, but their content is processed.
        N.B. Recursive function
        :param contents: dict of all content
        :return: list of separated json objects (~ all elements)
        """
        if not contents:
            return []

        result = []
        for content in contents:
            if content["type"] == PACKAGE_TYPE:
                result += self.get_all_elements(content["contents"])
            else:
                result += [content]
        return result

    def _existing_entity(self, _id) -> Entity | None:
        """
        Returns Entity for the given id if exists
        :param _id: id of the Entity
        :return: Entity if found, None otherwise
        """
        return self._entity_ids.get(_id)

    def add_entity(self, element: dict):
        """
        Creates a new Entity and adds it to the Graph
        :param element: dict with all properties
        """
        if element["order"] == "2":  # saving for generalization set names
            self._additional_entities[element["id"]] = element["name"]

        entity = self._existing_entity(element["id"])
        if entity:  # this entity was already created by relation
            entity.update(element)
        else:  # entity with this id does not exist
            entity = Entity(element)
            self._entity_ids[entity.id] = entity
        if entity.stereotype in self._entities:
            self._entities[entity.stereotype].append(entity)
        else:
            self._entities[entity.stereotype] = [entity]

    def _get_entity(self, _id: str) -> Entity:
        """
        Returns an Entity for the given id
        :param _id: id of the Entity
        :return: Entity object
        """
        entity = self._existing_entity(_id)
        if entity:
            return entity

        # entity with this id does not exist yet
        new_entity = Entity.init_from_id(_id)
        self._entity_ids[new_entity.id] = new_entity
        return new_entity

    def _existing_relation(self, _id) -> Relation | Generalization | None:
        """
        Returns Relation | Generalization for the given id if exists
        :param _id: id of the Relation | Generalization
        :return: Generalization if found, None otherwise
        """
        return self._relation_ids.get(_id)

    def add_relation(self, element: dict):
        """
        Creates a new Relation or Generalization and adds it to the Graph
        :param element: dict with all properties
        """
        # determine from- and to- entities and create them if needed
        _type = element["type"]
        if _type == GENERAL_TYPE:
            _from, _to = Generalization.get_ids(element)
        else:  # _type == RELATION_TYPE:
            _from, _to = Relation.get_ids(element)

        # N.B.: Here we ignore all Generalizations between Relations
        # N.B.: Also could be (None, None) in case of export issues
        # Test: GeneralizationRelation
        if _from and _to:
            entity_from = self._get_entity(_from)
            entity_to = self._get_entity(_to)

            # now it is safe to create a relation, e.g. both nodes exist
            if _type == GENERAL_TYPE:
                # check if this generalization was created by GeneralizationSet
                relation = self._existing_relation(element["id"])
                if relation:
                    relation.update(element, entity_from, entity_to)
                else:
                    relation = Generalization(element, entity_from, entity_to)
            else:
                relation = Relation(element, entity_from, entity_to)
                _type: EdgeType = relation.type

                # N.B.: invert part_of because of Visual Paradigm policy and plugin issues
                if _type == PART_OF_TYPE and relation.is_aggregation_from():
                    if self._verbalize:
                        self.logger.warning(f"Invert PartOf relation {relation.id}")
                    relation.invert()
                    entity_from, entity_to = entity_to, entity_from

            self._relations[_type].append(relation)
            self._relation_ids[relation.id] = relation

            # create link between nodes
            entity_from.add_outgoing(_type, relation.id)
            entity_to.add_incoming(_type, relation.id)

    def _get_generalization(self, _id: str) -> Generalization:
        """
        Returns a Generalization for the given id
        :param _id: id of the Generalization
        :return: Generalization object
        """
        generalization = self._existing_relation(_id)
        if generalization:
            return generalization

        # Generalization with this id does not exist
        new_generalization = Generalization.init_from_id(_id)
        self._relation_ids[new_generalization.id] = new_generalization
        return new_generalization

    def add_generalization_set(self, element: dict) -> str:
        """
        Creates a new GeneralizationSet and adds it to the Graph
        :param element: dict with all properties
        :return: id of the created GeneralizationSet
        """
        generalizations = [self._get_generalization(_id) for _id in GeneralizationSet.get_ids(element)]
        generalization_set = GeneralizationSet(element, generalizations, self._additional_entities)
        self._generalization_set_ids[generalization_set.id] = generalization_set
        for generalization in generalizations:
            generalization.add_to_set(generalization_set.id)
        return generalization_set.id

    def attach_view(self, view: View) -> bool:
        """
        Adds the given View to the corresponding Element
        :param view: View object that already exists
        :return: True, if View was added to the Element
        """
        element: BasicDict = view.element
        if not element:
            return False
        if element["type"] == CLASS_TYPE:
            self._entity_ids[element["id"]].add_view(view)
        elif element["type"] == GEN_SET_TYPE:
            self._generalization_set_ids[element["id"]].add_view(view)
        elif element["type"] != PACKAGE_TYPE:
            # N.B.: Here we ignore all Generalizations between Relations
            # Test: GeneralizationRelation
            if element["id"] in self._relation_ids:
                self._relation_ids[element["id"]].add_view(view)
            else:
                return False
        return True

    """
    ------------------------------------------------------------
    Exporting functions
    ------------------------------------------------------------
    """

    def to_json(self) -> dict:
        project_json = Element.to_json(self)
        project_json["model"] = self._model.to_json()

        element_list = []
        if self._entity_ids:
            for entity in self._entity_ids.values():
                element_list.append(entity.to_json())

        if self._relation_ids:
            for relation in self._relation_ids.values():
                element_list.append(relation.to_json())

        if self._generalization_set_ids:
            for generalization_set in self._generalization_set_ids.values():
                element_list.append(generalization_set.to_json())

        project_json["model"]["contents"] += element_list
        project_json["diagrams"] = [diagram.to_json() for diagram in self._diagrams.values()]

        return project_json

    def to_expo(self, max_height: int, max_width: int) -> dict:
        """
        Exports the current project to the Expo format
        :param max_height: maximum height of the canvas
        :param max_width: maximum width of the canvas
        :return: dict with the Expo project
        """
        result = {
            "graph": {"nodes": [], "links": []},
            "origin": self.to_json(),
            "constraints": []
        }

        height = max_height
        width = max_width
        if self._entity_ids:
            for entity in self._entity_ids.values():
                entity_dict = entity.to_expo()
                height = max(height, entity_dict["y"])
                width = max(width, entity_dict["x"])
                result["graph"]["nodes"].append(entity_dict)

        if height > max_height > 0:
            for entity in result["graph"]["nodes"]:
                entity["y"] = entity["y"] * (max_height - 10) // height
        if width > max_width > 0:
            for entity in result["graph"]["nodes"]:
                entity["x"] = entity["x"] * (max_width - 10) // width

        if self._relation_ids:
            for relation in self._relation_ids.values():
                result["graph"]["links"].append(relation.to_expo())
        result["graph"]["links"] = self._expo_links_postprocessing(result["graph"]["links"])

        for generalization_set in self._generalization_set_ids.values():
            result["constraints"].append(generalization_set.to_expo())

        return result

    @staticmethod
    def _expo_links_postprocessing(links: list) -> list:
        """
        Postprocessing of the links for the Expo format
        so that multiple links between nodes are displayed correctly
        """
        connections = {}
        double_links = {}
        for link in links:
            if link["source"]+link["target"] not in connections:
                if link["target"]+link["source"] not in connections:
                    connections[link["source"]+link["target"]] = link
                else:
                    connections[link["target"] + link["source"]]["name"] += " | " + link["name"]
                    connections[link["target"] + link["source"]]["fullName"] += " | " + link["fullName"]
                    if link["target"] + link["source"] not in double_links:
                        double_links[link["target"] + link["source"]] = link
                        double_links[link["target"] + link["source"]]["name"] = ""
                        double_links[link["target"] + link["source"]]["fullName"] = ""
            else:
                connections[link["source"]+link["target"]]["name"] += " | " + link["name"]
                connections[link["source"]+link["target"]]["fullName"] += " | " + link["fullName"]
        return list(connections.values()) + list(double_links.values())

    def __str__(self):
        result = "\n----------------------------------------------------------------------"
        result += f"\nCurrent internal structure:"
        result += f"\nNumber of relations: {len(self._relation_ids.values())}"
        result += f"\nincluding {len(self._relations['PartOf'])} part-of relations, "
        result += f"\n          {len(self._relations['Generalization'])} generalizations, "
        result += f"\n          {len(self._relations['Relation'])} ordinary relations. "
        if self._entity_ids:
            for entity in self._entity_ids.values():
                result += "\n" + str(entity)
                incoming, outgoing = entity.get_all_edges()
                for edge in incoming:
                    relation = self._relation_ids[edge]
                    result += f"\n\t<- [{relation}] {relation.from_entity.name}"
                for edge in outgoing:
                    relation = self._relation_ids[edge]
                    result += f"\n\t-> [{relation}] {relation.to_entity.name}"
        if self._generalization_set_ids:
            result += "\nGeneralization sets:"
            for generalization_set in self._generalization_set_ids.values():
                result += f"\n{generalization_set}"
        result += "\n----------------------------------------------------------------------"
        return result

    def to_row(self):
        return [
            len(self._entity_ids.values()),
            len(self._relation_ids.values()),
            len(self._relations['PartOf']),
            len(self._relations['Generalization']),
        ]

    """
    ------------------------------------------------------------
    Functions for changing the structure
    ------------------------------------------------------------
    """

    def _remove_views(self, views: List[View]):
        """
        Removes all given Views from the corresponding Diagrams
        :param views: List of Views to be removed
        """
        for view in views:
            diagram_id = view.diagram_id
            self._diagrams[diagram_id].del_element(view.id)

    def delete_generalization_set(self, _id: str):
        """
        Removes GeneralizationSet by id
        :param _id: id of GeneralizationSet
        """
        generalization_set = self._generalization_set_ids.pop(_id)
        self._remove_views(generalization_set.views)
        for generalization in generalization_set.generalizations:
            self._relation_ids[generalization.id].remove_from_set()

    def delete_relation(self, _id: str):
        """
        Removes Relation by id
        :param _id: id of Relation | Generalization
        """
        # remove from dictionaries
        relation = self._relation_ids.pop(_id)
        _type = relation.type
        self._relations[_type].remove(relation)

        # delete views
        self._remove_views(relation.views)

        # remove from outgoing
        self._entity_ids[relation.from_entity.id].del_outgoing(_type, relation.id)
        # remove from incoming
        self._entity_ids[relation.to_entity.id].del_incoming(_type, relation.id)

        if _type == GENERAL_TYPE:
            # remove from generalization set
            if relation.set:
                generalization_set = self._generalization_set_ids[relation.set]
                # delete completeness if there was any
                # and remove generalization from the set
                generalization_set.del_generalization(relation)
                if len(generalization_set.generalizations) < 2:
                    # if generalization set has only 2 generalizations
                    # it does not make sense to keep it
                    self.delete_generalization_set(generalization_set.id)

    def delete_entity(self, _id: str):
        """
        Removes Entity by id
        :param _id: id of Entity
        """
        if _id in self._entity_ids:
            entity = self._entity_ids[_id]

            # remove relations
            for relation in copy.copy(entity.get_in_edges()):
                self.delete_relation(relation)
            for relation in copy.copy(entity.get_out_edges()):
                self.delete_relation(relation)

            # pop entity from dictionary
            self._entity_ids.pop(_id)
            if entity.stereotype in self._entities:
                self._entities[entity.stereotype].remove(entity)
            # remove views
            self._remove_views(entity.views)

    def _create_relation(self, source: Entity, target: Entity, source_view: View,
                         target_view: View, diagram_id: str, name: str = None,
                         cardinality_from: str = None, cardinality_to: str = None):
        """
        Creates relation and adds it to the diagram
        :param source: Entity that is source for the relation
        :param target: Entity that is target for the relation
        :param source_view: View of the source Entity
        :param target_view: View of the target Entity
        :param diagram_id: id of the diagram to which the elements are added
        :param cardinality_from: cardinality for the 'from' end
        :param cardinality_to: cardinality for the 'to' end
        :param name: name of the Relation
        """
        # create Relation
        relation_dict = Relation.init_relation(source.id, target.id, name, cardinality_from, cardinality_to)
        relation_id = relation_dict["id"]
        self.add_relation(relation_dict)

        # create view for Relation
        relation_view = View.create_edge_view(True, relation_id, source_view.id, target_view.id, diagram_id,
                                              [source_view.get_center(), target_view.get_center()])
        self._relation_ids[relation_id].add_view(relation_view)
        self._diagrams[diagram_id].add_element(relation_view)

    def _create_enumeration_and_relation(self, source: Entity, literals: List, name: str, diagram_id: str):
        """
        Creates enumeration and corresponding relation, adds all to the diagram
        :param source: Entity that is source for the generalization set
        :param literals: List of literals to be added to Enumeration
        :param name: Name of Enumeration
        :param diagram_id: id of the diagram to which the elements are added
        """
        # create Enumeration
        enumeration_dict = Entity.init_enumeration(literals, name=name)
        enumeration_id = enumeration_dict["id"]
        self.add_entity(enumeration_dict)
        target = self._entity_ids[enumeration_id]

        # create view for Enumeration
        enumeration_view = View.create_entity_view(enumeration_id, diagram_id,
                                                   x=source.get_view(diagram_id).get_x() + DEFAULT_WIDTH + 50,
                                                   y=source.get_view(diagram_id).get_y() + DEFAULT_HEIGHT + 50,
                                                   height=DEFAULT_HEIGHT + len(literals) * ATTRIBUTE_HEIGHT)
        self._entity_ids[enumeration_id].add_view(enumeration_view)
        self._diagrams[diagram_id].add_element(enumeration_view)

        self._create_relation(source, target, source.get_view(diagram_id), enumeration_view,
                              diagram_id, cardinality_to="1")

    def _clear_abstracted_entities(self):
        """
        Removes Entities that lost their Kinds during abstraction process
        """
        if self._ids_to_be_abstracted:
            for _id in self._ids_to_be_abstracted:
                self.delete_entity(_id)
            self._ids_to_be_abstracted = []

    """
    ------------------------------------------------------------
    Operators functions: cluster, focus
    ------------------------------------------------------------
    """

    def focus(self, node: str, hop: int):
        """
        Focuses on the given node and
        shows only those concepts that are connected to it with the given hop
        :param node: id of the node for focusing
        :param hop: number of links within the focus
        """
        if node not in self._entity_ids:
            raise ValueError(f"Concept with id='{node}' does not exist")

        focus_nodes = self._get_focus_nodes(node, hop)
        other_nodes = self._entity_ids.keys() - focus_nodes
        for node in other_nodes:
            self.delete_entity(node)

    def _get_focus_nodes(self, node: str, hop: int) -> List[str]:
        """
        Returns a set of nodes that are connected to the given node with the given hop
        :param node: id of the node for focusing
        :param hop: number of links within the focus
        :return: list of ids of nodes in focus
        """
        nodes = [node]
        idx = 0
        while hop > 0:
            length = len(nodes)
            while idx < length:
                for edge in self._entity_ids[nodes[idx]].get_out_edges():
                    nodes.append(self._relation_ids[edge].to_entity.id)
                for edge in self._entity_ids[nodes[idx]].get_in_edges():
                    nodes.append(self._relation_ids[edge].from_entity.id)
                idx += 1
            hop -= 1
        return nodes

    def cluster(self, node: str):
        """
        Implements the relator-centric clustering approach
        :param node: id of the RELATOR node for focusing
        """
        if node not in self._entity_ids:
            raise ValueError(f"Concept with id='{node}' does not exist")

        if self._entity_ids[node].stereotype != ClassStereotype.RELATOR.value:
            # raise ValueError(f"Concept with id='{node}' is not a RELATOR")
            self.logger.warning(f"Concept with id='{node}' is not a RELATOR")
        else:  # cluster on relator
            cluster_nodes = self._get_cluster_nodes(node)
            other_nodes = self._entity_ids.keys() - cluster_nodes
            for node in other_nodes:
                self.delete_entity(node)

    def _get_cluster_nodes(self, relator: str) -> List[str]:
        """
        Returns a set of nodes that belong to the cluster
        :param node: id of the RELATOR node
        :return: list of ids of nodes in cluster
        """
        nodes = self._get_bottom_hierarchy(relator)  # in case the relator has a hierarchy
        mediated = []
        for node in nodes:
            for edge in self._entity_ids[node].get_out_edges(edge_type="Relation"):
                if self._relation_ids[edge].stereotype == RelationStereotype.MEDIATION.value:
                    # include mediated entities in list
                    mediated.append(self._relation_ids[edge].to_entity.id)

        for node in mediated:
            if self._entity_ids[node].stereotype == ClassStereotype.RELATOR.value:  # if mediates other RELATOR
                nodes.extend([n for n in self._get_cluster_nodes(node) if n not in nodes])  # recursion
            elif self._entity_ids[node].stereotype in NON_SORTAL_STEREOTYPES:
                new_nodes = self._get_bottom_hierarchy(node)  # get all bottom concepts
                for new_node in new_nodes:  # for each find a top hierarchy
                    nodes.extend([n for n in self._get_top_hierarchy(new_node) if n not in nodes])
            elif self._entity_ids[node].stereotype in SORTAL_STEREOTYPES:
                nodes.extend([n for n in self._get_top_hierarchy(node) if n not in nodes]) # get top hierarchy
        return nodes

    def _get_top_hierarchy(self, node: str) -> List[str]:
        """
        Returns a list of nodes that include all concepts upto Kind level
        :param node: id of the node
        :return: list of ids of nodes in hierarchy starting from the given node
        """
        nodes = [node]
        idx = 0

        while idx < len(nodes):
            if self._entity_ids[nodes[idx]].stereotype and \
               (not self._entity_ids[nodes[idx]].stereotype in KINDS_STEREOTYPES):
                out_edges = self._entity_ids[nodes[idx]].get_out_edges(edge_type="Generalization")
                for out_edge in out_edges:
                    top_concept = self._relation_ids[out_edge].to_entity.id
                    nodes.extend([n for n in self._get_bottom_hierarchy(top_concept, out_edge) if n not in nodes])
            idx += 1
        return nodes

    def _get_bottom_hierarchy(self, node: str, desc_edge: str = "") -> List[str]:
        """
        Returns a list of bottom concepts in the hierarchy
        If desc_edge is given, returns only those concepts that are in the same GeneralizationSet
        :param node: id of the node
        :param desc_edge: id of the generalization edge, optional
        :return: list of ids of nodes in hierarchy starting from the given node
        """
        nodes = [node]
        if desc_edge:  # if there is an edge in which one we are interested
            set_id = self._relation_ids[desc_edge].set
            if not set_id:  # if it is not in GeneralizationSet
                nodes.append(self._relation_ids[desc_edge].from_entity.id)
            else:
                if self._generalization_set_ids[set_id].is_complete_and_disjoint():
                    gens = self._generalization_set_ids[set_id].generalizations
                    for gen in gens:  # for each Generalization in the set
                        nodes.append(self._relation_ids[gen.id].from_entity.id)
                else:  # if GS is not complete and disjoint
                    nodes.append(self._relation_ids[desc_edge].from_entity.id)
        else:  # return all concepts that are generalized to this one
            idx = 0
            while idx < len(nodes):
                if self._entity_ids[nodes[idx]].stereotype in NON_SORTAL_STEREOTYPES + [ClassStereotype.RELATOR.value]:
                    for edge in self._entity_ids[nodes[idx]].get_in_edges(edge_type="Generalization"):
                        nodes.append(self._relation_ids[edge].from_entity.id)
                idx += 1
        return nodes

    """
    ------------------------------------------------------------
    Functions for expand operator
    ------------------------------------------------------------
    """
    @staticmethod
    def _clear_name(name: str):
        """
        Prepare node name for indexing
        """
        return ''.join(filter(str.isalnum, name.lower()))

    def get_index(self, delimiter: str = INDEX_DELIMITER) -> list:
        """
        Returns a list of all nodes with their stereotypes
        """
        result = []
        for entity in self._entity_ids.values():
            result.append(f"{self._clear_name(entity.name)}{delimiter}{entity.stereotype}")
        return result

    def get_node_index(self, node: str) -> str:
        """
        Returns the index of the given node in the form:
        name + INDEX_DELIMITER + stereotype
        """
        if node not in self._entity_ids:
            return ""
        entity = self._entity_ids[node]
        return f"{self._clear_name(entity.name)}{INDEX_DELIMITER}{entity.stereotype}"

    def get_hierarchy(self, node: str) -> dict:
        """
        Returns the hierarchy of the node by the given index
        """
        result = {"nodes": {}, "sets": {}}
        nodes = []

        name, stereotype = node.split(INDEX_DELIMITER)
        for entity in self._entities[stereotype]:
            if self._clear_name(entity.name) == name:
                nodes.append(entity)
                break

        idx = 0
        while idx < len(nodes):
            node_idx = self.get_node_index(nodes[idx].id)
            if node_idx not in result["nodes"]:
                result["nodes"][node_idx] = []
            for edge in nodes[idx].get_in_edges(edge_type="Generalization"):
                generalization = self._relation_ids[edge]
                nodes.append(self._entity_ids[generalization.from_entity.id])
                from_idx = self.get_node_index(generalization.from_entity.id)
                result["nodes"][node_idx].append(from_idx)
                if generalization.set:
                    set_id = generalization.set
                    if set_id not in result["sets"]:
                        result["sets"][set_id] = {"to": node_idx, "from": [],
                                                  "complete": self._generalization_set_ids[set_id].is_complete(),
                                                  "disjoint": self._generalization_set_ids[set_id].is_disjoint()}
                    result["sets"][set_id]["from"].append(from_idx)
            idx += 1

        return result

    def expand(self, node_id: str, hierarchy: dict):
        """
        Adds the given hierarchy to the graph
        :param node_id: id of the node to which the hierarchy should be added
        :param hierarchy: hierarchy to add
        """
        nodes = hierarchy["nodes"]
        sets = hierarchy["sets"]
        diagrams = [view.diagram_id for view in self._entity_ids[node_id].views]

        # create index for nodes
        node_idx = {}
        x, y = None, None
        for node in nodes.keys():
            node_idx[node] = self._create_similar_node(node, diagrams, x, y)
            # Only because of visualization purposes
            x = node_idx[node].get_view(diagrams[0]).get_x()
            y = node_idx[node].get_view(diagrams[0]).get_y() + 1.2*DEFAULT_HEIGHT

        # create index for generalizations
        gen_idx = {}
        for node, children in nodes.items():
            for child in children:
                gen_idx[node+child] = self._create_similar_relation(node_idx[node], node_idx[child], diagrams)

        for gen_set in sets.values():
            self._create_similar_set(gen_idx, gen_set, diagrams)

    def _create_similar_node(self, node_idx: str, diagrams: List[str], x: int | None, y: int | None) -> Entity:
        """
        Creates a similar node to the one with the given index
        :param node_idx: index of the node to create a similar one to
        :param diagrams: diagrams to add the node to
        :return: created Entity
        """
        node = None
        name, stereotype = node_idx.split(INDEX_DELIMITER)
        if stereotype in self._entities:
            for n in self._entities[stereotype]:
                if self._clear_name(n.name) == name:
                    node = n
                    break

        if not node:  # there is no similar node
            node_dict = Entity.init_entity(name=name.capitalize(), stereotype=stereotype)
            node_id = node_dict["id"]
            self.add_entity(node_dict)
            # create views
            for diagram_id in diagrams:
                if x and y:
                    node_view = View.create_entity_view(node_id, diagram_id, x=x, y=y)
                else:
                    node_view = View.create_entity_view(node_id, diagram_id)
                self._entity_ids[node_id].add_view(node_view)
                self._diagrams[diagram_id].add_element(node_view)
            node = self._entity_ids[node_id]
        return node

    def _create_similar_relation(self, to_node: Entity, from_node: Entity, diagrams: List[str]):
        """
        Creates a generalization between the given nodes
        :param to_node: general node
        :param from_node: specific node
        :param diagrams: diagrams to add the node to
        """
        for edge in to_node.get_in_edges(edge_type="Generalization"):
            if self._relation_ids[edge].from_entity.id == from_node.id:
                return self._relation_ids[edge]

        relation_dict = Generalization.init_generalization(from_node.id, to_node.id)
        relation_id = relation_dict["id"]
        self.add_relation(relation_dict)

        for diagram_id in diagrams:
            source_view = from_node.get_view(diagram_id)
            target_view = to_node.get_view(diagram_id)
            relation_view = View.create_edge_view(False, relation_id, source_view.id, target_view.id, diagram_id,
                                                  [source_view.get_center(), target_view.get_center()])
            self._relation_ids[relation_id].add_view(relation_view)
            self._diagrams[diagram_id].add_element(relation_view)

        return self._relation_ids[relation_id]

    def _create_similar_set(self, gen_idx: dict, gen_set: dict, diagrams: List[str]):
        """
        Creates a generalization set between the given nodes
        :param gen_idx: index of the generalizations
        :param gen_set: generalization set to create
        :param diagrams: diagrams to be added to
        """
        generalizations = []
        for node in gen_set["from"]:
            generalizations.append(gen_idx[gen_set["to"]+node])

        if not generalizations[0].set:
            gen_set_dict = GeneralizationSet.init_generalization_set(
                generalizations, gen_set["complete"], gen_set["disjoint"])
            gen_set_id = self.add_generalization_set(gen_set_dict)

            for diagram_id in [view.diagram_id for view in generalizations[0].views]:
                gen_set_view = View.create_set_view(gen_set_id, diagram_id, generalizations[0].views[0].get_x(),
                                                    generalizations[0].views[0].get_y())
                self._generalization_set_ids[gen_set_id].add_view(gen_set_view)
                self._diagrams[diagram_id].add_element(gen_set_view)

    """
    ------------------------------------------------------------
    Abstraction functions
    ------------------------------------------------------------
    """

    def create_relation_from_existing(self, relation: Relation | Generalization,
                                      new_from: Entity = None, new_to: Entity = None, new_name: str = None,
                                      role_from: str = None, role_to: str = None) -> str:
        """
        Creates a copy of the existing Relation, optionally moves it to new from- or to- Entity
        takes care about ids, views, adds to diagrams and dictionaries
        :param relation: original Relation | Generalization
        :param new_from: move out-edge to this Entity if given
        :param new_to: move in-edge to this Entity if given
        :param new_name: new relation name, if given
        :param role_from: new role name for from-end, if given
        :param role_to: new role name for to-end, if given
        :return: id of new relation
        """
        new_relation = copy.deepcopy(relation)
        new_id = new_relation.update_ids(self._diagrams)  # update ids also in views
        # adding to dictionaries
        self._relation_ids[new_id] = new_relation
        _type = new_relation.type
        self._relations[_type].append(new_relation)
        # move relation if needed
        if new_from or new_to:
            new_relation.move(new_from, new_to, self._diagrams, new_name, role_from, role_to)
        # adds relation to new Entities
        self._entity_ids[new_relation.from_entity.id].add_outgoing(_type, new_id)
        self._entity_ids[new_relation.to_entity.id].add_incoming(_type, new_id)
        return new_id

    def _check_for_existence_by_prototype(self, mult_relations: bool, relation: Relation | Generalization,
                                          from_entity: Entity = None, to_entity: Entity = None) \
            -> Relation | Generalization | None:
        """
        Check if similar relation already exists for the given Entity, either for from_entity, or for to_entity
        :param mult_relations: create several relations between the same Entities
        :param relation: Relation | Generalization
        :param from_entity: Entity for checking the relation, so that to_entity is fixed
        :param to_entity: Entity for checking the relation, so that from_entity is fixed
        :return: Relation|Generalization if found or None
        """
        if not to_entity:
            to_entity = relation.to_entity
        if not from_entity:
            from_entity = relation.from_entity

        return self._check_for_relation_existence(mult_relations, from_entity, to_entity, relation.type, relation.name)

    def _check_for_relation_existence(self, mult_relations: bool, from_entity: Entity, to_entity: Entity,
                                      relation_type=RELATION_TYPE, relation_name: str = "") \
            -> Relation | Generalization | None:
        """
        Check if relation exists between from- and to- entities
        :param mult_relations: create several relations between the same Entities
        :param from_entity: one Node of the relation
        :param to_entity: another Node of the relation
        :param relation_name: name to be checked
        :return: Relation | Generalization if found
        """
        for candidate_id in set(from_entity.out_edges[relation_type] + to_entity.in_edges[relation_type] +
                                from_entity.in_edges[relation_type] + to_entity.out_edges[relation_type]):
            if candidate_id in self._relation_ids:
                candidate_relation = self._relation_ids[candidate_id]
                if ((candidate_relation.from_entity.id == from_entity.id) and
                    (candidate_relation.to_entity.id == to_entity.id)) or (
                        (candidate_relation.to_entity.id == from_entity.id) and
                        (candidate_relation.from_entity.id == to_entity.id)):
                    if not mult_relations:
                        return candidate_relation
                    elif relation_name and (
                            (not candidate_relation.name) or (
                            len(set.intersection(set(candidate_relation.name.lower().split(" ")),
                                                 set(relation_name.lower().split(" ")))
                                ) > 0)):
                        return candidate_relation
        return None

    def _move_relation(self, is_from: bool, mult_relations: bool, relation: Relation | Generalization,
                       entity: Entity, new_name: str = None, new_role: str = None):
        """
        Additional function that helps with role names, relations names, etc. when moving relations
        :param is_from: if True, changing from node
        :param mult_relations: create several relations between the same Entities
        :param relation: Relation or Generalization that should be moved
        :param entity: new to- or from- node
        :param new_name: new name for the relation if given
        :param new_role: new role name if given
        """
        if is_from:
            existing_relation = self._check_for_existence_by_prototype(mult_relations, relation, from_entity=entity)
            if not existing_relation:
                new_id = self.create_relation_from_existing(relation, new_from=entity,
                                                            new_name=new_name, role_from=new_role)
                self._relation_ids[new_id].relax_cardinality_to()
            else:
                # update existing relation
                if (not mult_relations) and relation.name and (existing_relation.name != relation.name):
                    if existing_relation.name and (relation.name not in existing_relation.name):
                        existing_relation.name += f" ({relation.name})"
                    elif not existing_relation.name:
                        existing_relation.name = relation.name
                existing_relation.clear_role_from()
                existing_relation.set_minimal_cardinality_from(relation.get_cardinality_from())
                existing_relation.set_minimal_cardinality_to(relation.get_cardinality_to())
        else:
            existing_relation = self._check_for_existence_by_prototype(mult_relations, relation, to_entity=entity)
            if not existing_relation:
                new_id = self.create_relation_from_existing(relation, new_to=entity,
                                                            new_name=new_name, role_to=new_role)
                self._relation_ids[new_id].relax_cardinality_from()
            else:
                # update existing relation
                if (not mult_relations) and relation.name and (existing_relation.name != relation.name):
                    if existing_relation.name and (relation.name not in existing_relation.name):
                        existing_relation.name += f" ({relation.name})"
                    elif not existing_relation.name:
                        existing_relation.name = relation.name
                existing_relation.clear_role_to()
                existing_relation.set_minimal_cardinality_from(relation.get_cardinality_from())
                existing_relation.set_minimal_cardinality_to(relation.get_cardinality_to())

    def _abstract_generalization(self, generalization: Generalization, long_names: bool, mult_relations: bool):
        """
        Additional function that moves all relations from the specific entity upwards
        """
        general_entity = generalization.to_entity
        specific_entity = generalization.from_entity
        self.logger.info(f"Abstracting generalization from {specific_entity.name} to {general_entity.name}")
        self.fold_entity(specific_entity, long_names, mult_relations)

        for in_id in copy.copy(specific_entity.in_edges[RELATION_TYPE] + specific_entity.in_edges[PART_OF_TYPE]):
            role = None if self._relation_ids[in_id].role_to else specific_entity.name
            self._move_relation(False, mult_relations, self._relation_ids[in_id], general_entity, new_role=role)
        for out_id in copy.copy(specific_entity.out_edges[RELATION_TYPE] + specific_entity.out_edges[PART_OF_TYPE]):
            role = None if self._relation_ids[out_id].role_from else specific_entity.name
            self._move_relation(True, mult_relations, self._relation_ids[out_id], general_entity, new_role=role)

        # remove other entity only if there is no other up-going links
        if specific_entity.has_other_up_edges():
            self.delete_relation(generalization.id)
            if general_entity.stereotype not in NON_SORTAL_STEREOTYPES:
                self._ids_to_be_abstracted.append(specific_entity.id)
        else:
            self.delete_entity(specific_entity.id)

    def _process_generalization_set(self, gs: GeneralizationSet, long_names: bool, mult_relations: bool):
        """
        Process GeneralizationSet abstraction if found
        :param gs: GeneralizationSet object
        :param long_names: create names with 's
        :param mult_relations: create several relations between the same Entities
        """
        literals = []
        diagram_id = gs.views[0].diagram_id if gs.views else gs.generalizations[0].to_entity.views[0].diagram_id
        source = gs.generalizations[0].to_entity
        complete_disjoint = gs.is_complete_and_disjoint()
        gs_name = gs.name
        self.logger.info(f"Process generalization set to {source.name}")

        for generalization in copy.copy(gs.generalizations):
            literals.append(generalization.from_entity.name)
            self._abstract_generalization(generalization, long_names, mult_relations)

        if complete_disjoint:
            literals_obj = [Literal(literal).to_json() for literal in literals]

            # check if there is already enumeration
            for _id in copy.copy(source.get_out_edges()):
                candidate_entity = self._relation_ids[_id].to_entity
                if candidate_entity.stereotype == ClassStereotype.ENUMERATION.value:
                    literals_obj += candidate_entity.rest["literals"]
                    if len(candidate_entity.get_out_edges()) + len(candidate_entity.get_in_edges()) > 1:
                        self.delete_relation(_id)
                    else:
                        self.delete_entity(candidate_entity.id)
            # create enumeration and relation to it
            self._create_enumeration_and_relation(source, literals_obj, gs_name, diagram_id)

    def abstract_hierarchy(self, generalization: Generalization, long_names: bool, mult_relations: bool):
        """
        Abstract Generalization relation
        :param generalization: Generalization that should be abstracted
        :param long_names: create names with 's
        :param mult_relations: create several relations between the same Entities
        """
        general_entity = generalization.to_entity

        if general_entity.stereotype in NON_SORTAL_STEREOTYPES:  # R2 implementation
            self.logger.info(f"Pushing all relations from {general_entity.name} down")
            self.fold_entity(general_entity, long_names, mult_relations, part_of_only=True)

            # all specific entities that should receive new relations
            specific_entities = [self._relation_ids[_id].from_entity for _id in general_entity.in_edges[GENERAL_TYPE]]
            new_role = general_entity.name
            for in_id in general_entity.in_edges[RELATION_TYPE]:
                relation = self._relation_ids[in_id]
                for entity in specific_entities:
                    self._move_relation(False, mult_relations, relation, entity, new_role=new_role)
            for out_id in general_entity.out_edges[RELATION_TYPE]:
                relation = self._relation_ids[out_id]
                for entity in specific_entities:
                    self._move_relation(True, mult_relations, relation, entity, new_role=new_role)
            self.delete_entity(general_entity.id)

        else:  # need to go upwards
            if generalization.set:  # R4-H5
                self._process_generalization_set(self._generalization_set_ids[generalization.set],
                                                 long_names, mult_relations)
            else:  # R3-H4
                self._abstract_generalization(generalization, long_names, mult_relations)

    def abstract_hierarchies(self, long_names: bool, mult_relations: bool):
        """
        Abstract all generalizations that could be found in the graph
        """
        self.logger.debug("Abstracting all hierarchies")
        while self._relations[GENERAL_TYPE]:
            self.abstract_hierarchy(self._relations[GENERAL_TYPE][0], long_names, mult_relations)
        self._clear_abstracted_entities()

    def abstract_parthood(self, relation: Relation, long_names: bool, mult_relations: bool):
        """
        Abstract given parthood relation
        :param relation: Relation to be abstracted
        :param long_names: modify names with 's
        :param mult_relations: create multiple relations between Entities
        """
        whole_entity = relation.to_entity
        part_entity = relation.from_entity
        if whole_entity.id == part_entity.id:
            self.logger.error(ERR_RECURSION + part_entity.name)
            self.delete_relation(relation.id)
            return

        self.logger.info(f"Abstracting part_of from {part_entity.name} to {whole_entity.name}")
        role_name = part_entity.name
        self.fold_entity(part_entity, long_names, mult_relations)
        # In case of recursion previous line could lead to deletion of whole_entity
        if whole_entity.id not in self._entity_ids:
            self.logger.error(ERR_RECURSION + f"{part_entity.name}, {whole_entity.name}")
            if relation.id in self._relation_ids:
                self.delete_relation(relation.id)
            return

        new_name = ""

        if relation.stereotype == RelationStereotype.COMPONENT_OF.value:
            role_name = None  # no roles if componentOf
            whole_entity.add_attribute(part_entity.name)  # add part_entity as attribute
            if long_names:
                new_name = f"{whole_entity.name}'s {part_entity.name} "

        # move all relations from part-entity to this whole-entity
        for in_id in part_entity.in_edges[RELATION_TYPE]:
            candidate_relation = self._relation_ids[in_id]
            if candidate_relation.stereotype != RelationStereotype.TERMINATION.value or \
                    relation.is_essential():
                if (not long_names) or (candidate_relation.from_entity.stereotype in NOT_OBJECTS):
                    name = candidate_relation.name
                else:
                    name = new_name + candidate_relation.name if candidate_relation.name else new_name
                self._move_relation(False, mult_relations, candidate_relation, whole_entity, name, role_name)
                self._relation_ids[in_id].rest["properties"][1]["cardinality"] = "1"

        for out_id in part_entity.out_edges[RELATION_TYPE]:
            candidate_relation = self._relation_ids[out_id]
            if (not long_names) or (candidate_relation.from_entity.stereotype in NOT_OBJECTS):
                name = candidate_relation.name
            else:
                name = new_name + candidate_relation.name if candidate_relation.name else new_name
            self._move_relation(True, mult_relations, candidate_relation, whole_entity, name, role_name)
            self._relation_ids[out_id].rest["properties"][0]["cardinality"] = "1"

        for in_id in part_entity.in_edges[PART_OF_TYPE]:
            candidate_relation = self._relation_ids[in_id]
            if candidate_relation.stereotype == RelationStereotype.MEMBER_OF.value:
                self._move_relation(False, mult_relations, candidate_relation, whole_entity)

        # remove other entity only if there is no other up-going links
        if part_entity.has_other_up_edges():
            self.delete_relation(relation.id)
        else:
            self.delete_entity(part_entity.id)

    def abstract_parthoods(self, long_names: bool, mult_relations: bool):
        """
        Abstract all parthood relations that could be found in the graph
        """
        self.logger.debug("Abstracting all parthood relations")
        idx = 0
        while idx < len(self._relations[PART_OF_TYPE]):
            relation = self._relations[PART_OF_TYPE][idx]
            if relation.stereotype != RelationStereotype.MEMBER_OF.value:
                self.abstract_parthood(relation, long_names, mult_relations)
            else:
                idx += 1

    def _get_aspect_stocks(self, entity: Entity) -> (List, List):
        """
        Calculates all upper level concepts and incoming relations that should be moved
        :param entity: Entity that represent an Aspect
        :returns: List of stocks, in_relations
        """
        stocks, in_relations = [], []

        # determine lists of to-entities
        for _id in entity.out_edges[GENERAL_TYPE]:
            out_relation = self._relation_ids[_id]
            stocks.append(out_relation.to_entity)

        # determine incoming relations that should be moved up
        for _id in entity.in_edges[RELATION_TYPE]:
            in_relation = self._relation_ids[_id]
            if in_relation.from_entity.stereotype in ENDURANT_OR_DATATYPE:
                in_relations.append(in_relation)

        return stocks, in_relations

    def _get_aspect_sources(self, entity: Entity) -> (List, List):
        """
        Calculates all needed sources and outgoing relations
        :param entity: Entity that represent an Aspect
        :returns: List of sources, out_relations
        """
        sources, out_relations = [], []

        # determine lists of from-entities and relations that should be duplicated
        for _id in entity.out_edges[RELATION_TYPE]:
            if _id in self._relation_ids:
                out_relation = self._relation_ids[_id]
                if out_relation.stereotype in [RelationStereotype.MEDIATION.value,
                                               RelationStereotype.CHARACTERIZATION.value]:
                    sources.append(out_relation.to_entity)
                elif out_relation.to_entity.stereotype in ENDURANT_OR_DATATYPE:
                    out_relations.append(out_relation)

        return sources, out_relations

    def _get_aspect_participations(self, entity: Entity) -> (List, List):
        """
        Calculates all Events and relations to them
        :param entity: Entity that represent an Aspect
        :returns: List of events, relations
        """
        events, relations = [], []

        # determine if there are any Events that manifested this aspect, (Event, Relation)
        for _id in entity.in_edges[RELATION_TYPE]:
            in_relation = self._relation_ids[_id]
            if in_relation.stereotype == RelationStereotype.MANIFESTATION.value and \
                    in_relation.from_entity.stereotype == ClassStereotype.EVENT.value:
                events.append((in_relation.from_entity, in_relation))

        return events, relations

    def abstract_aspect(self, entity: Entity, long_names: bool, mult_relations: bool, keep_relators: bool):
        """
        Abstract the given aspect entity.
        N.B. Recursive function for processing chains of externally dependent aspects
        :param entity: Entity that represent an Aspect
        :param long_names: modify names with 's
        :param mult_relations: create multiple relations between Entities
        :param keep_relators: keep relators with more than MIN_RELATORS_DEGREE relations
        """
        self.logger.info(f"Abstracting {entity.name}")
        # if we need to abstract this Aspect according to the given parameters
        if (not keep_relators) or (entity.get_number_of_edges() < MIN_RELATORS_DEGREE):

            self.fold_entity(entity, long_names, mult_relations)
            for _id in entity.in_edges[RELATION_TYPE]:
                in_relation = self._relation_ids[_id]
                if in_relation.from_entity.stereotype in ASPECTS:
                    # There is a chain of aspects: recursive call
                    self.abstract_aspect(in_relation.from_entity, long_names, mult_relations, keep_relators)

            stocks, in_relations = self._get_aspect_stocks(entity)
            sources, out_relations = self._get_aspect_sources(entity)
            events, relations = self._get_aspect_participations(entity)

            # Move all incoming to the upper level of hierarchy
            for in_relation in in_relations:
                for stock in stocks:
                    if not self._check_for_existence_by_prototype(mult_relations, in_relation, to_entity=stock):
                        new_id = self.create_relation_from_existing(in_relation, new_to=stock, role_to=entity.name)
                        self._relation_ids[new_id].relax_cardinality_to()

            # A1
            for out_relation in out_relations:
                for source in sources:
                    if not long_names:
                        name = out_relation.name if out_relation.name else entity.name
                    else:
                        name = f"{source.name}'s {out_relation.role_from if out_relation.role_from else entity.name}"
                        if out_relation.name:
                            name += f" {out_relation.name}"
                    if not self._check_for_existence_by_prototype(mult_relations, out_relation, from_entity=source):
                        new_id = self.create_relation_from_existing(out_relation, new_from=source,
                                                                    role_from="", new_name=name)
                        self._relation_ids[new_id].relax_cardinality_to()
                        self._relation_ids[new_id].rest["properties"][0]["cardinality"] = None

            # Create relations between sources (see A1) if there was no any
            for i in range(0, len(sources) - 1):
                for j in range(i+1, len(sources)):
                    diagram_ids = sources[i].get_all_diagrams().intersection(sources[j].get_all_diagrams())
                    if not self._check_for_relation_existence(mult_relations, sources[i],
                                                              sources[j], relation_name=entity.name):
                        for diagram_id in diagram_ids:
                            self._create_relation(sources[i], sources[j], sources[i].get_view(diagram_id),
                                                  sources[j].get_view(diagram_id), diagram_id, name=entity.name)

            # A2
            for event, relation in zip(events, relations):
                for source in sources:
                    relation.stereotype = RelationStereotype.PARTICIPATION.value
                    if not self._check_for_existence_by_prototype(mult_relations, relation,
                                                                  from_entity=source, to_entity=event):
                        new_id = self.create_relation_from_existing(relation, new_from=source, new_to=event,
                                                                    role_from="", role_to="")
                        self._relation_ids[new_id].rest["properties"][1]["cardinality"] = "1"
                        self._relation_ids[new_id].rest["properties"][0]["cardinality"] = None

            self.delete_entity(entity.id)

    def abstract_aspects(self, long_names: bool, mult_relations: bool, keep_relators: bool):
        """
        Abstract all relators, modes and qualities that could be found in the graph
        """
        self.logger.debug("Abstracting all aspects")
        for aspect in ASPECTS:
            if aspect in self._entities:
                for aspect_entity in copy.copy(self._entities[aspect]):
                    self.abstract_aspect(aspect_entity, long_names, mult_relations, keep_relators)

    def fold_entity(self, entity: Entity, long_names: bool, mult_relations: bool, part_of_only: bool = False):
        """
        Collapses all parthoods and hierarchies to the Entity itself
        N.B. Recursive function
        :param entity: Entity that should be folded
        :param long_names: modify names with 's
        :param mult_relations: create multiple relations between Entities
        :param part_of_only: if True, then only part_of relations are folded
        """
        self.logger.info(f"Folding {entity.name}")
        if self._add_to_stack(entity.name):

            # abstract parthood
            idx = 0
            while idx < len(entity.in_edges[PART_OF_TYPE]):
                _id = entity.in_edges[PART_OF_TYPE][idx]
                relation = self._relation_ids[_id]
                if relation.stereotype != RelationStereotype.MEMBER_OF.value:
                    self.abstract_parthood(relation, long_names, mult_relations)
                else:
                    idx += 1

            # hierarchy abstraction
            if not part_of_only:
                # get all from NON_SORTALS
                for out_id in copy.copy(entity.out_edges[GENERAL_TYPE]):
                    if out_id in self._relation_ids:
                        out_relation = self._relation_ids[out_id]
                        if out_relation.to_entity.stereotype in NON_SORTAL_STEREOTYPES:
                            self.abstract_hierarchy(out_relation, long_names, mult_relations)
                # get all from lower levels
                while entity.in_edges[GENERAL_TYPE]:
                    _id = entity.in_edges[GENERAL_TYPE][0]
                    self.abstract_hierarchy(self._relation_ids[_id], long_names, mult_relations)

            self._clear_abstracted_entities()
            self._stack.pop(-1)

    def fold(self, node: str, long_names: bool, mult_relations: bool):
        """
        Implements folding functionality for the given node id
        """
        self.fold_entity(self._entity_ids[node], long_names, mult_relations)
