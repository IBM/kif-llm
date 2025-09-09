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

### Simple Disambiguator

```python
from kbel.disambiguators.simple import SimpleDisambiguator
from kif_lib import Search

# Term to link entities
label = "Python"

# Using KIF Wikidata Searcher
searcher = Search('wikidata-wapi', limit=10)
disambiguator = SimpleDisambiguator('simple')

results = disambiguator.disambiguate_item(label, searcher)
print(results)
```

### Similarity Disambiguator
```python
from kbel.disambiguators.similarity import SimilarityDisambiguator

disambiguator = SimilarityDisambiguator('sim')
results = disambiguator.disambiguate_item(label, searcher, limit=1, sentence="Python is used for coding")
print(results)
```

### LLM Disambiguator

```python
from kbel.disambiguators.llm import LLM_Disambiguator

# Using ChatGPT models
disambiguator = LLM_Disambiguator(
    disambiguator_name='llm',
    model_name='gpt-4',
    model_provider='openai',
    model_apikey='YOUR_API_KEY',
    model_endpoint='https://api.openai.com/v1'
)

# Using KIF DBPedia Searcher
searcher = Search('dbpedia', limit=10)

results = disambiguator.disambiguate_item(label, searcher, sentence="Python is used for coding")
print(results)
```

or

```python
from kbel.disambiguators.llm import LLM_Disambiguator

# Using a LangChain model. For instance, IBM WatsonX
model = ChatWatsonx(
    model_id='meta-llama/llama-3-3-70b-instruct',
    apikey=YOUR_API_KEY, # type: ignore
    url='YOUR_LLM_API_ENDPOINT', # type: ignore
    project_id='YOUR_WATSONX_PROJECT_ID',
)
disambiguator = LLM_Disambiguator(disambiguator_name='llm', model=model)

# Using KIF DBPedia Searcher
searcher = Search('dbpedia', limit=10)

results = disambiguator.disambiguate_item(label, searcher, sentence="Python is used for coding")
print(results)
```

## License

Released under the [Apache-2.0 license](./LICENSE).
