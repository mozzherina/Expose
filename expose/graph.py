from abc import ABC, abstractmethod


class BaseGraph(ABC):

    @abstractmethod
    def to_expo(self, max_height: int, max_width: int) -> dict:
        """
        Converts the graph to the expo format
        :param max_height: maximum height of the graph
        :param max_width: maximum width of the graph
        :return: graph in the expo format
        """
        pass

    @abstractmethod
    def to_json(self) -> dict:
        """
        Converts the graph to the json format
        :return: graph in the json format
        """
        pass

    @abstractmethod
    def focus(self, node: str, hop: int):
        """
        Focuses on the given node and
        shows only those concepts that are connected to it with the given hop
        :param node: id of the node for focusing
        :param hop: number of links within the focus
        """
        pass

    @abstractmethod
    def cluster(self, node: str):
        """
        Implements the relator-centric clustering approach
        :param node: id of the node for focusing
        """
        pass

    @abstractmethod
    def delete_entity(self, node: str):
        """
        Deletes the entity from the graph
        :param node: id of the node
        """
        pass

    @abstractmethod
    def delete_relation(self, relation: str):
        """
        Deletes the entity from the graph
        :param relation: id of the relation
        """
        pass

    @abstractmethod
    def expand(self, node: str, hierarchy: dict):
        """
        Expands the given node with the given hierarchy
        :param node: id of the node
        :param hierarchy: hierarchy to be added to the node
        """
        pass

    @abstractmethod
    def fold(self, node: str, long_names: bool, mult_relations: bool):
        """
        Folds the given node
        :param node: id of the node
        :param long_names: whether to use long names with 's
        :param mult_relations: whether to create multiple relations
        """
        pass

    @abstractmethod
    def abstract_parthoods(self, long_names: bool, mult_relations: bool):
        """
        Abstracts all parthoods
        :param long_names: whether to use long names with 's
        :param mult_relations: whether to create multiple relations
        """
        pass

    @abstractmethod
    def abstract_aspects(self, long_names: bool, mult_relations: bool, keep_relators: bool):
        """
        Abstracts all aspects
        :param long_names: whether to use long names with 's
        :param mult_relations: whether to create multiple relations
        :param keep_relators: whether to keep relators
        """
        pass

    @abstractmethod
    def abstract_hierarchies(self, long_names: bool, mult_relations: bool):
        """
        Abstracts all hierarchies
        :param long_names: whether to use long names with 's
        :param mult_relations: whether to create multiple relations
        """
        pass

    @abstractmethod
    def get_node_index(self, node: str):
        """
        Returns the index of the node in the graph
        name + INDEX_DELIMITER + stereotype
        :param node: id of the node
        """
        pass

    @abstractmethod
    def get_index(self, delimiter: str):
        """
        Returns the index of ALL nodes in the graph
        name + INDEX_DELIMITER + stereotype
        :param delimiter: delimiter for the index
        """
        pass


# TODO: implementation for the ttl format
class TTLGraph(BaseGraph):
    def __init__(self, graph: dict):
        super().__init__()
        self.graph = graph

    def to_expo(self, max_height: int, max_width: int) -> dict:
        raise NotImplementedError

    def to_json(self) -> dict:
        raise NotImplementedError

    def focus(self, node: str, hop: int):
        raise NotImplementedError

    def cluster(self, node: str):
        raise NotImplementedError

    def delete_entity(self, _id: str):
        raise NotImplementedError

    def delete_relation(self, _id: str):
        raise NotImplementedError

    def expand(self, node: str, hierarchy: dict):
        raise NotImplementedError

    def fold(self, node: str, long_names: bool, mult_relations: bool):
        raise NotImplementedError

    def abstract(self, level: str):
        raise NotImplementedError

    def get_node_index(self, node: str):
        raise NotImplementedError

    def get_index(self, delimiter: str):
        raise NotImplementedError

    def abstract_aspects(self, long_names: bool, mult_relations: bool, keep_relators: bool):
        raise NotImplementedError

    def abstract_hierarchies(self, long_names: bool, mult_relations: bool):
        raise NotImplementedError

    def abstract_parthoods(self, long_names: bool, mult_relations: bool):
        raise NotImplementedError
