<p align="center"><img src="./docs/_assets/favicon.svg" width="200"></p>

### Install
```shell
$ pip install -e .
```
or

```shell
$ poetry install
```

### Using the API
```python
from kifqa import KIFQA
from kif_lib import Store, Search
from kifqa.stores import WikidataStore

kif_wiki_kbqa = KIFQA(
    store=Store('wikidata'),
    search=Search('wikidata-wapi'),
    model_name='mistralai/mistral-medium-2505',
    model_provider='ibm',
    model_params= {
        'temperature': 0.0,
        'project_id': os.getenv('WATSONX_PROJECT_ID')
    },
    model_apikey=os.getenv('LLM_API_KEY'),
    model_endpoint=os.getenv('LLM_API_ENDPOINT')
)

stmts = kif_wiki_kbqa.run(question='What is the nationality of anthony bailey', )

for stmt in stmts:
    print(stmt)
```
> Statement(Item(IRI('http://www.wikidata.org/entity/Q4772057')), ValueSnak(Property(IRI('http://www.wikidata.org/entity/P27'), ItemDatatype()), Item(IRI('http://www.wikidata.org/entity/Q145'))))

### CLI Examples:
```shell
$ kifqa list-stores
```
> Available stores:</br>
> dbpedia-extension: &nbsp;&nbsp;&nbsp;&nbsp; DBpedia query service store extension</br>
> pubchem-extension: &nbsp;&nbsp;&nbsp;PubChem SPARQL store extension</br>
> wikidata-extension: &nbsp;&nbsp;&nbsp;&nbsp; Wikidata query service store extension


```shell
$ kifqa query -q "Where did Ozzy Osbourne die?" -c config/wikidata/config.yaml --store wikidata --search wikidata-wapi
```
> (**Statement** (**Item** [Ozzy Osbourne](http://www.wikidata.org/entity/Q133151)) (**ValueSnak** (**Property** [place of death](http://www.wikidata.org/entity/P20)) (**Item** [Birmingham](http://www.wikidata.org/entity/Q2256))))


```shell
$ kifqa query -q "Where was Ozzy Osbourne born?" -c config/wikidata/config.yaml --store dbpedia --search dbpedia
```
> (**Statement** (**Item** [Ozzy Osbourne](http://dbpedia.org/resource/Ozzy_Osbourne)) (**ValueSnak** (**Property** [birthPlace](http://dbpedia.org/ontology/birthPlace)) (**Item** [Warwickshire](http://dbpedia.org/resource/Warwickshire))))

> (**Statement** (**Item** [Ozzy Osbourne](http://dbpedia.org/resource/Ozzy_Osbourne)) (**ValueSnak** (**Property** [birthPlace](http://dbpedia.org/ontology/birthPlace)) (**Item** [Marston Green](http://dbpedia.org/resource/Marston_Green))))


```shell
$ kifqa query -q "What is the mass of benzene?" -c config/pubchem/config.yaml --store pubchem --search pubchem-pug
```
> (**Statement** (**Item** [Benzene](http://rdf.ncbi.nlm.nih.gov/pubchem/compound/CID241)) (**ValueSnak** (**Property** [mass](http://www.wikidata.org/entity/P2067)) 78.047 [dalton](http://www.wikidata.org/entity/Q483261)))
