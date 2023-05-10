import os.path
import traceback
import uvicorn
import logging
import sys
import requests
import json
import csv
import time

from fastapi import FastAPI, UploadFile, Query, HTTPException, Form, File
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
from typing import List, Annotated
from copy import deepcopy
from collections import deque
from github import Github

from expose import *
from expose.models import *
from expose.graph import TTLGraph
from expose.schema import ABSTRACTION_TYPE
from expose.project.jsongraph import JSONGraph


# TODO: remove comments before release
def setup_custom_logger(name, level=logging.INFO):
    formatter = logging.Formatter(fmt='%(levelname)-8s %(asctime)s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    # handler = logging.FileHandler(LOG_FILE_NAME, mode='w+')
    # handler.setFormatter(formatter)
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    custom_logger = logging.getLogger(name)
    custom_logger.setLevel(level)
    # custom_logger.addHandler(handler)
    custom_logger.addHandler(screen_handler)
    return custom_logger


logger = setup_custom_logger(LOG_NAME, logging.DEBUG)


app = FastAPI()

# add CORS support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/get_logs")
async def get_logs():
    """
    Returns logs of the last session
    """
    return FileResponse(LOG_FILE_NAME)


@app.get("/health")
async def health():
    """
    Returns health status
    """
    return {"status": "OK"}


@app.post("/load")
async def load(
        file: UploadFile | None = None,
        url: Annotated[str, Form()] = "",
        in_format: Annotated[str, Form()] = "",
        out_format: Annotated[str, Form()] = "",
        height: Annotated[int, Form()] = 0,
        width: Annotated[int, Form()] = 0
):
    """
    Loads model from file or url into graph,
    and returns graph object according to the format
    :param file: file with model
    :param url: url with model
    :param in_format: format of the model, should be 'json' or 'ttl'
    :param out_format: format of the graph, should be 'expo' or 'json'
    :param height: height of the canvas
    :param width: width of the canvas
    """
    logger.debug("Loading model...")

    if (not file) and (not url):
        raise HTTPException(status_code=400, detail=ERR_NOT_ENOUGH_PARAMS)
    if file and url:
        logger.warning(WARN_FILE_AND_URL_PARAMS)
    if in_format not in ["json", "ttl"]:
        raise HTTPException(status_code=400,
                            detail=ERR_NOT_CORRECT_PARAMS + " 'in_format' should be 'json' or 'ttl'.")
    if out_format not in ["expo", "json"]:
        raise HTTPException(status_code=400,
                            detail=ERR_NOT_CORRECT_PARAMS + " 'out_format' should be 'expo' or 'json'.")

    try:
        # the next line throws an exception if the model is not in the right format
        data = load_from_file(file, in_format) if file else load_from_url(url, in_format)
        new_graph = JSONGraph(data) if in_format == "json" else TTLGraph(data)
        return new_graph.to_expo(height, width) if out_format == "expo" else new_graph.to_json()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def load_from_file(file: UploadFile, in_format: str):
    """
    Loads the model from file.
    Raises exception if the model is not in the right format
    :param file: file with model
    :param in_format: format of the model, should be 'json' or 'ttl'
    """
    logger.debug("Loading model from the file...")

    try:
        if in_format == "json":
            return json.loads(file.file.read())
        else:
            # TODO: upload of ttl files
            raise NotImplementedError
    except Exception as e:
        logger.error(e)
        raise Exception(ERR_BAD_FILE) from e
    finally:
        file.file.close()


def load_from_url(url: str, in_format: str):
    """
    Loads model from url
    Raises exception if the model is not in the right format
    :param url: url with model
    :param in_format: format of the model, should be 'json' or 'ttl'
    """
    logger.debug("Loading model from the url...")
    logger.info(f"Downloading model from the url: {url}")

    try:
        if in_format == "json":
            return requests.get(url, allow_redirects=True).json()
        else:
            # TODO: upload of ttl files
            raise NotImplementedError
    except requests.exceptions.Timeout | requests.exceptions.ConnectionError as e:
        logger.error(e.response.text)
        raise Exception(ERR_BAD_CONNECTION) from e


def data_checks(data: GraphModel):
    """
    Checks if the parameters is correct
    :param data: data to check
    """
    if not data.origin:
        raise HTTPException(status_code=400, detail=ERR_NO_MODEL)
    if data.in_format not in ["json", "ttl"]:
        raise HTTPException(status_code=400,
                            detail=ERR_NOT_CORRECT_PARAMS + " 'in_format' should be 'json' or 'ttl'.")
    if data.out_format not in ["expo", "json"]:
        raise HTTPException(status_code=400,
                            detail=ERR_NOT_CORRECT_PARAMS + " 'out_format' should be 'expo' or 'json'.")


@app.post("/focus")
async def focus(data: FocusModel):
    """
    Focuses on the given node and
    shows only those concepts that are connected to it with the given hop
    :param data: dict with node and hop
    """
    data_checks(data)
    try:
        graph = JSONGraph(data.origin) if data.in_format == "json" else TTLGraph(data.origin)
        graph.focus(data.node, data.hop)
        return graph.to_expo(data.height, data.width) if data.out_format == "expo" else graph.to_json()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/cluster")
async def cluster(data: BasicModel):
    """
    Implements the relator-centric clustering approach
    :param data: dict with node
    """
    data_checks(data)
    try:
        graph = JSONGraph(data.origin) if data.in_format == "json" else TTLGraph(data.origin)
        graph.cluster(data.node)
        return graph.to_expo(data.height, data.width) if data.out_format == "expo" else graph.to_json()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/delete")
async def delete(data: DeleteModel):
    """
    Deletes concept or relation from the graph
    :param data: dict with element_id and element_type
    """
    data_checks(data)
    if data.element_type not in ["node", "link"]:
        raise HTTPException(status_code=400,
                            detail=ERR_NOT_CORRECT_PARAMS + " 'element_type' should be 'node' or 'link'.")

    try:
        graph = JSONGraph(data.origin) if data.in_format == "json" else TTLGraph(data.origin)
        if data.element_type == "node":
            graph.delete_entity(data.element_id)
        elif data.element_type == "link":
            graph.delete_relation(data.element_id)
        else:
            # TODO: place here implementation of constraints deletion
            pass
        return graph.to_expo(data.height, data.width) if data.out_format == "expo" else graph.to_json()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# TODO: alternatively consider https://developer.oxforddictionaries.com/
@app.get("/define")
async def define(
        concept: str,
        number_of_def: int = DEFINE_MAX_NUMBER
):
    """
    Implements showing the dictionary definition
    :param concept: concept to define
    :param number_of_def: number of definitions to show
    :return: definitions of the concept, {"concept": ..., "definition": []}
    """
    result = {"concept": concept, "definition": []}
    response = requests.get(DEFINE_API_URL + concept)
    if response.ok:
        try:
            meanings = response.json()[0]["meanings"]
            for meaning in meanings:
                if meaning["partOfSpeech"] == "noun":
                    for n in range(0, number_of_def):
                        if n >= len(meaning["definitions"]):
                            break
                        result["definition"].append(meaning["definitions"][n]["definition"])
            return result
        except Exception:
            logger.error(f"No definition found for {concept}.")
            return result
    else:
        return result


@app.put("/index")
async def index():
    """
    (Re)Builds catalog index
    Additional route
    """
    if os.path.exists(INDEX_FILE_NAME):
        os.remove(INDEX_FILE_NAME)
    create_catalog_index()


def get_git_contents(model_names: list = None) -> list:
    """
    Loads all or selected models from the GitHub repository
    :param model_names: list of model names to load, optional
    """
    logger.debug("Loading models from the GitHub repository...")
    start = time.time()

    git = Github(GIT_TOKEN)
    all_repos = list(filter(lambda r: r.full_name.endswith(GIT_REPO), git.get_user(GIT_USER).get_repos()))
    repository = all_repos[0] if all_repos else None
    if not repository:
        logger.error(f"Not able to find repository {GIT_REPO} for the user {GIT_USER}")
        raise HTTPException(status_code=400, detail=f"Not able to find repository {GIT_REPO} for the user {GIT_USER}")

    if model_names:
        contents = [repository.get_contents(name) for name in model_names]
    else:
        all_models = repository.get_contents("models")
        contents = [repository.get_contents(model.path + "/ontology.json") for
                    model in all_models if model.path.split("/")[-1] not in IGNORED_MODELS]

    end = time.time()
    logger.debug("Repository was collected in {:.2f} seconds.".format(end - start))
    return contents


def create_catalog_index() -> dict:
    """
    Creates catalog index
    :return: index dictionary
    """
    name_index = {}
    contents = get_git_contents()
    if not contents:
        logger.error(f"Not able to find any models in the repository {GIT_REPO} for the user {GIT_USER}")
        return name_index

    logger.debug("Indexing models...")
    start = time.time()

    for content in contents:
        logger.debug(f"Adding concepts from {content.path}, index size = {len(name_index)}.")
        graph_json = json.loads(content.decoded_content.decode())
        graph_index = JSONGraph(graph_json, verbalize=False).get_index()
        for concept in graph_index:
            if concept not in name_index:
                name_index[concept] = []
            name_index[concept].append(content.path)

    end = time.time()
    logger.debug("Indexing took  {:.2f} seconds.".format(end - start))

    with open(INDEX_FILE_NAME, 'w', newline='', encoding='utf-8') as f:
        json.dump(name_index, f)
    return name_index


@app.post("/expand")
async def expand(data: ExpandModel):
    """
    Expand existing concept with information from the catalog
    :param data: dict with node and limit
    """
    data_checks(data)
    if not os.path.exists(INDEX_FILE_NAME):
        name_index = create_catalog_index()
    else:
        with open(INDEX_FILE_NAME, 'r', newline='', encoding='utf-8') as f:
            name_index = json.load(f)
    if not name_index:
        raise HTTPException(status_code=400, detail=ERR_NO_INDEX)

    try:
        graph = JSONGraph(data.origin) if data.in_format == "json" else TTLGraph(data.origin)
        idx = graph.get_node_index(data.node)
        if (not idx) or (idx not in name_index):
            logger.info(f"{idx} for {data.node} is not found in the index.")
            return graph.to_expo(data.height, data.width) if data.out_format == "expo" else graph.to_json()

        left_nodes = data.limit
        contents = get_git_contents(name_index[idx])
        for content in contents:
            graph_json = json.loads(content.decoded_content.decode())
            graph_hierarchy_dict = JSONGraph(graph_json, verbalize=False).get_hierarchy(idx)
            left_nodes -= len(graph_hierarchy_dict["nodes"])
            graph.expand(data.node, graph_hierarchy_dict)
            if (data.limit > 0) and (left_nodes <= 0):
                break
        return graph.to_expo(data.height, data.width) if data.out_format == "expo" else graph.to_json()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/fold")
async def fold(data: FoldModel):
    """
    Folds the given node
    :param data: dict with node
    """
    data_checks(data)
    try:
        graph = JSONGraph(data.origin) if data.in_format == "json" else TTLGraph(data.origin)
        graph.fold(data.node, data.long_names, data.mult_relations)
        return graph.to_expo(data.height, data.width) if data.out_format == "expo" else graph.to_json()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/abstract")
async def abstract(data: AbstractModel):
    """
    Abstracts the given graph
    :param data: dict with abstraction type
    """
    data_checks(data)
    for abs_type in data.abs_type:
        if abs_type not in ABSTRACTION_TYPE:
            raise HTTPException(status_code=400, detail=ERR_UNKNOWN_ABS)

    # TODO: adapt the code to the TTLGraph
    try:
        graph = JSONGraph(data.origin) if data.in_format == "json" else TTLGraph(data.origin)
        # write_to_stat_file(graph.to_row(), graph.name)
        for abs_type in data.abs_type:
            match abs_type:
                case "parthood":
                    graph.abstract_parthoods(data.long_names, data.mult_relations)
                case "aspects":
                    graph.abstract_aspects(data.long_names, data.mult_relations, data.keep_relators)
                case "hierarchy":
                    graph.abstract_hierarchies(data.long_names, data.mult_relations)
            # write_to_stat_file(graph.to_row(), graph.name)
        return graph.to_expo(data.height, data.width) if data.out_format == "expo" else graph.to_json()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


"""
def write_to_stat_file(graph_stat: list, name: str, params: str = ""):
    with open(STAT_FILE_NAME, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([name, params] + graph_stat)
"""


if __name__ == "__main__":
    """
    if not os.path.exists(STAT_FILE_NAME):
        with open(STAT_FILE_NAME, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["name", "params", "number_of_classes", "number_of_all_relations",
                             "number_of_part_of_relations", "number_of_generalizations"])
    """

    uvicorn.run(app, port=API_PORT, host="0.0.0.0")
