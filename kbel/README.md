# Knowledge Base Entity Linking (KBEL)

KBEL is a framework for linking terms embedded in a given context to entities in a target knowledge base. See examples [here](./examples/demo.ipynb).

KBEL leverages [KIF](https://github.com/IBM/kif)'s abstractions for handling knowledge base features. The main abstractions used are:
- **Search**: Provides an interface to query a knowledge base and retrieve candidate entities or properties.
- **Item**: Represents an entity in the knowledge base (e.g., a Wikidata or DBpedia item) and provides access to its label, description, and IRI.
- **Property**: Represents a property or relationship between entities in the knowledge base.
---

## Supports multiple disambiguation strategies:
  - `SimpleDisambiguator`: returns the top-1 candidate.
  - `SimilarityDisambiguator`: selects candidates based on embedding similarity (cosine, dot product, or Euclidean distance).
  - `LLM_Disambiguator`: leverages a large language model to choose the most relevant candidate given a sentence and optional context.

It is **extensible**: Easily implement new disambiguation methods by subclassing `Disambiguator`.

---

## Quickstart

```python
from kbel.disambiguators import Disambiguator
```

### Simple Disambiguator

```python
from kbel.disambiguators.simple import SimpleDisambiguator
from kif_lib import Search

# Term to link entities
label = "Python"

# Using KIF Wikidata Searcher
searcher = Search('wikidata-wapi', limit=10)
disambiguator = Disambiguator('simple')

results = disambiguator.disambiguate_item(label, searcher)
for result in results:
    print (result)
```

### Similarity Disambiguator
```python
from kbel.disambiguators.similarity import SimilarityDisambiguator

disambiguator = Disambiguator('sim')
results = disambiguator.disambiguate_item(label, searcher, limit=1, sentence="Python is used for coding")
for result in results:
    print (result)
```

### LLM Disambiguator

```python
from kbel.disambiguators.llm import LLM_Disambiguator

# Using ChatGPT models
disambiguator = Disambiguator(
    'llm',
    model_name='gpt-4',
    model_provider='openai',
    model_apikey='YOUR_API_KEY',
    model_endpoint='https://api.openai.com/v1'
)

# Using KIF DBPedia Searcher
searcher = Search('dbpedia', limit=10)

results = disambiguator.disambiguate_item(label, searcher, sentence="Python is used for coding")
for result in results:
    print (result)
```

or

```python
from kbel.disambiguators.llm import LLM_Disambiguator

# Using a LangChain model. For instance, IBM WatsonX
model = ChatWatsonx(
    model_id='meta-llama/llama-3-3-70b-instruct',
    apikey=YOUR_API_KEY,
    url='YOUR_LLM_API_ENDPOINT',
    project_id='YOUR_WATSONX_PROJECT_ID',
)
disambiguator = Disambiguator('llm', model=model)

# Using KIF DBPedia Searcher
searcher = Search('dbpedia', limit=10)

results = disambiguator.disambiguate_item(label, searcher, sentence="Python is used for coding")
for result in results:
    print (result)
```

## License

Released under the [Apache-2.0 license](./LICENSE).
