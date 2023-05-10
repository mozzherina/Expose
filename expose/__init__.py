from decouple import config
from typing import Final

"""
------------------------------------------------------------
General constants specified in .env
------------------------------------------------------------
"""
API_PORT: Final[int] = int(config("API_PORT"))
LOG_NAME: Final[str] = config("LOG_NAME")
LOG_FILE_NAME: Final[str] = config("LOG_FILE_NAME")
STAT_FILE_NAME: Final[str] = config("STAT_FILE_NAME")
DEFINE_API_URL: Final[str] = config("DEFINE_API_URL")
DEFINE_MAX_NUMBER: Final[int] = int(config("DEFINE_MAX_NUMBER"))
EXPAND_MAX_NUMBER: Final[int] = int(config("EXPAND_MAX_NUMBER"))

"""
------------------------------------------------------------
Constants for Expo configuration
------------------------------------------------------------
"""
GRAPH_BASIC_COLOUR: Final[str] = config("GRAPH_BASIC_COLOUR")
GRAPH_RELATOR_COLOUR: Final[str] = config("GRAPH_RELATOR_COLOUR")
GRAPH_MODE_COLOUR: Final[str] = config("GRAPH_MODE_COLOUR")
GRAPH_OBJECT_COLOUR: Final[str] = config("GRAPH_OBJECT_COLOUR")
GRAPH_ENUMERATION_COLOUR: Final[str] = config("GRAPH_ENUMERATION_COLOUR")
GRAPH_EVENT_COLOUR: Final[str] = config("GRAPH_EVENT_COLOUR")
GRAPH_RELATOR_SYMBOL: Final[str] = config("GRAPH_RELATOR_SYMBOL")
GRAPH_MODE_SYMBOL: Final[str] = config("GRAPH_MODE_SYMBOL")
GRAPH_ENUMERATION_SYMBOL: Final[str] = config("GRAPH_ENUMERATION_SYMBOL")
GRAPH_EVENT_SYMBOL: Final[str] = config("GRAPH_EVENT_SYMBOL")
GRAPH_BASIC_SYMBOL: Final[str] = config("GRAPH_BASIC_SYMBOL")
GRAPH_STROKE_WIDTH: Final[int] = int(config("GRAPH_STROKE_WIDTH"))
GRAPH_STROKE_DASHARRAY: Final[int] = int(config("GRAPH_STROKE_DASHARRAY"))

"""
------------------------------------------------------------
Parameters for building index file
------------------------------------------------------------
"""
INDEX_FILE_NAME: Final[str] = config("INDEX_FILE_NAME")
INDEX_DELIMITER: Final[str] = config("INDEX_DELIMITER")
IGNORED_MODELS: list = config("IGNORED_MODELS").split(",")
GIT_USER: Final[str] = config("GIT_USER")
GIT_REPO: Final[str] = config("GIT_REPO")
GIT_TOKEN: Final[str] = config("GIT_TOKEN")

"""
------------------------------------------------------------
Constants for abstraction
------------------------------------------------------------
"""
LONG_NAMES: Final[bool] = config("LONG_NAMES") == "True"
MULT_RELATIONS: Final[bool] = config("MULT_RELATIONS") == "True"
KEEP_RELATORS: Final[bool] = config("KEEP_RELATORS") == "True"

MIN_RELATORS_DEGREE: Final[int] = int(config("MIN_RELATORS_DEGREE"))
ID_LENGTH: Final[int] = int(config("ID_LENGTH"))

"""
------------------------------------------------------------
Constants for JSON configuration
------------------------------------------------------------
"""
ATTRIBUTE_HEIGHT: Final[int] = int(config("ATTRIBUTE_HEIGHT"))
DEFAULT_WIDTH: Final[int] = int(config("DEFAULT_WIDTH"))
DEFAULT_HEIGHT: Final[int] = int(config("DEFAULT_HEIGHT"))
DEFAULT_X: int = int(config("DEFAULT_X"))  # could be changed during execution
DEFAULT_Y: int = int(config("DEFAULT_Y"))  # could be changed during execution

"""
------------------------------------------------------------
Constants that are used as messages to the user
------------------------------------------------------------
"""
# errors
ERR_NOT_ENOUGH_PARAMS: Final[str] = "Not enough parameters are given. Please, check the documentation."
ERR_NOT_CORRECT_PARAMS: Final[str] = "The parameters are not correctly specified."
ERR_BAD_FILE: Final[str] = "The given file cannot be read. Please, check if it is in the right format."
ERR_BAD_CONNECTION: Final[str] = "The model cannot be downloaded. Please, check the internet connection."
ERR_BAD_ORIGIN: Final[str] = "The model cannot be downloaded. Please, check the given file or the url."
ERR_RECURSION: Final[str] = "The recursion was detected. Please, check the following concept: "
ERR_NO_MODEL: Final[str] = "The model is not loaded. Please, load the model first."
ERR_NO_INDEX: Final[str] = "The index file is not loaded. Please, make sure the repository is available."
ERR_UNKNOWN_ABS: Final[str] = "The abstraction is not known. Please, check the documentation."

# warnings
WARN_FILE_AND_URL_PARAMS: Final[str] = "Both the file with data and the url are given. The url will be ignored."

# information
