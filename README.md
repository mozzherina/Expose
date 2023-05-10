# ExpO Framework

## Expose: ExpO REST API Server
An API service for performing transformation operations over Ontology Driven Conceptual Models.

The server is running [here](https://expose.eng.unibz.it/health).

If you are interested to know more, feel free to open an issue to provide feedback on the project or reach our team members for more specific cases:

* [Elena Romanenko](https://github.com/mozzherina)
* [Konstantin Romanenko](https://github.com/astricus)
* [Diego Calvanese](http://www.inf.unibz.it/~calvanese/)
* [Giancarlo Guizzardi](https://people.utwente.nl/g.guizzardi)

___

## Endpoints
Endpoint documentation is available at `/docs` and `/redoc` endpoints

### Examples of requests
Test if the server is running and accepts requests:
```shell script
[GET] http://host-name:port/health
```

Ask for 2 definitions (apply __define__) to the concept 'Mother'
```shell script
[GET] https://host-name:port/define?concept=Mother&number_of_def=2
```

Apply __abstraction__ (parthood and hierarchy) to the model
```shell script
[POST] http://host-name:port/abstract
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
As an example of the ondology-driven conceptual model you may take any model from the 
[OntoUML/UFO Catalog](https://github.com/OntoUML/ontouml-models/tree/master/models).

___
## If you want to run your own server

### Requirements
* Docker 20.10 or later
* GitHub account

### Installation
In general, you need only to run the `docker-compose` command. 
However, if you want to run `expand` operation, you will need to specify your credentials in `.env.example`.

```shell script
git clone git@github.com:mozzherina/Expose.git
cp .env.example .env
docker-compose --compatibility up -d
```

### Specifying credentials for GitHub
1. Create a fork from the [repository](https://github.com/OntoUML/ontouml-models/).
2. Go to your GitHub account and create an access token for this repository:
Your GitHub Profile / Settings / Developer Settings / Fine-grained Tokens / 
Generate new token.
3. In `env.example` change `GIT_USER` and `GIT_TOKEN` to your own values.

___
## If you want to cite this work

Please, refer to the [PURL](https://purl.org/expo/expose) and
cite the paper: 

Romanenko, E., Calvanese, D., Guizzardi, G.: ExpO: A Framework for Explaining
Ontology-Driven Conceptual Models. (2023) Manuscript submitted for publication.

