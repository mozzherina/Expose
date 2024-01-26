# ExpO: Towards Explaining Ontology-Driven Conceptual Models

## Expose: ExpO server
An API service for performing transformation operations over Ontology-Driven Conceptual Models.

The public server is running [here](https://expose.eng.unibz.it/health).

If you are interested to know more, feel free to open an issue to provide feedback on the project or reach our team members for more specific cases:

* [Elena Romanenko](https://github.com/mozzherina)
* [Diego Calvanese](http://www.inf.unibz.it/~calvanese/)
* [Giancarlo Guizzardi](https://people.utwente.nl/g.guizzardi)
* [Konstantin Romanenko](https://github.com/astricus)


### Contents

* [Endpoints](#endpoints)
* [Running your own server](#if-you-want-to-run-your-own-server)
* [Citing this work](#if-you-want-to-cite-this-work)

___

## Endpoints
A complete endpoint documentation is available at `/docs`.


### Health
Test if the server is running and accepts requests:
```shell script
[GET] https://host-name:port/health
```
The server should return:
```json
{"status":"OK"}
```


### Load
```shell script
[POST] https://host-name:port/load
```
Loads the model from file or url into graph, and returns graph object according to the format. 
If `out_format = expo` then:
```json
{
  "graph": {
    "nodes":  [...],
    "links": [...]
  },
  "origin": {ODCM_IN_JSON_FORMAT},
  "constraints": [...]
}
```
As an example of the ondology-driven conceptual model you may take any model from the
[OntoUML/UFO Catalog](https://github.com/OntoUML/ontouml-models/tree/master/models).


### Focus
```shell script
[POST] https://host-name:port/focus
```
with the following body:
```json
{
  "node": NODE_ID,
  "hop": 2,
  "in_format": "json",
  "out_format": "expo",
  "origin": {
    ODCM_IN_JSON_FORMAT
  }
}
```
Focuses on the given node and shows only those concepts that are connected to it within the given
number of hops (in this example no far than 2 relations away).


### Cluster
```shell script
[POST] https://host-name:port/cluster
```
with the following body:
```json
{
  "node": NODE_ID,
  "in_format": "json",
  "out_format": "expo",
  "origin": {
    ODCM_IN_JSON_FORMAT
  }
}
```
Implements the [relator-centric clustering](https://link.springer.com/article/10.1007/s10270-021-00919-5) 
approach to the given node.


### Define

Ask for 2 definitions for the concept `Mother`:
```shell script
[GET] https://host-name:port/define?concept=Mother&number_of_def=2
```
The result is returned to the user in the following format:
```json
{
    "concept": "Mother",
    "definition": [
        "A (human) female who has given birth to a baby",
        "A human female who parents an adopted or fostered child"
    ]
}
```


### Expand
```shell script
[POST] https://host-name:port/expand
```
with the following body:
```json
{
  "node": NODE_ID,
  "limit": 5,
  "in_format": "json",
  "out_format": "expo",
  "origin": {
    ODCM_IN_JSON_FORMAT
  }
}
```
Expand the existing concept with information from the [OntoUML/UFO Catalog](https://github.com/OntoUML/ontouml-models/), 
and returns about 5 new concepts.


### Abstract
```shell script
[POST] https://host-name:port/abstract
```
with the following body:
```json
{
  "abs_type": [
    "parthood",
    "hierarchy"
  ],
  "long_names": true,
  "mult_relations": false,
  "keep_relators": true,
  "in_format": "json",
  "out_format": "json",
  "origin": {
    PLACE_HERE_YOUR_ODCM
  }
}
```

Apply two types of [abstractions](https://link.springer.com/chapter/10.1007/978-3-031-05760-1_22) 
(parthood and hierarchy) to the model. 


### Fold
```shell script
[POST] https://host-name:port/fold
```
with the following body:
```json
{
  "node": NODE_ID,
  "long_names": true,
  "mult_relations": false,
  "in_format": "json",
  "out_format": "json",
  "origin": {
    PLACE_HERE_YOUR_ODCM
  }
}
```

Folds the given node (apply all types of abstractions but to the given node only).


### Delete
```shell script
[POST] https://host-name:port/fold
```
with the following body:
```json
{
  "element_id": RELATION_ID,
  "element_type": "link",
  "in_format": "json",
  "out_format": "expo",
  "origin": {
    PLACE_HERE_YOUR_ODCM
  }
}
```
Deletes the given node (`"element_type": "node"`) or relation from the model.


___
## If you want to run your own server

### Requirements
* Docker 20.10 or later
* GitHub account

### Installation
In general, you need only to run the `docker-compose` command. 
However, if you want to run `expand` operation, you will need to specify your GitHub credentials in `.env.example`.

```shell script
git clone git@github.com:mozzherina/Expose.git
cp .env.example .env
docker-compose --compatibility up -d
```

### Specifying credentials for GitHub
1. Create a fork from the [repository](https://github.com/OntoUML/ontouml-models/).
2. Go to your GitHub account and create an access token for this repository:
    ```
    Your GitHub Profile
       -> Settings
          -> Developer Settings
             -> Fine-grained Tokens
                -> Generate new token
    ```
    Generate a token for __Only selected repositories__ (specify the fork you have done on the first step), and give
    the following __Repository permissions__:
    ```
    Contents = read-only
    Metadata = read-only
    ```
3. In `.env.example` change `GIT_USER` and `GIT_TOKEN` to your own values.

___
## If you want to cite this work

Please, refer to the [PURL](https://w3id.org/ExpO/expose) and
cite the paper: 

Romanenko, E., Calvanese, D., Guizzardi, G.: ExpO: A Framework for Explaining
Ontology-Driven Conceptual Models. (2023) _Manuscript submitted for publication._

