# KIFQA API

This is a RESTful API over KIFQA, providing simplified access to queries, filters, and model condiguration.

## Start server
```bash
python app.py
```
The server will start on http://localhost:5000/.

## Methods

| Endpoint  | Method | Description                    |
| --------- | ------ | ------------------------------ |
| `/status` | GET    | Get system status              |
| `/config` | POST   | Update KIFQA LLM configuration |
| `/stores` | GET    | List available stores          |
| `/query`  | POST   | Run a query                    |
| `/filter` | POST   | Run a filter                   |


## Examples ##


#### Status ####
```bash
curl -X GET http://localhost:5000/status
```

#### Config ####
```bash
curl -X POST http://localhost:5000/config \
-H "Content-Type: application/json" \
-d '{
    "model_provider": "ibm",
    "model_name": "meta-llama/llama-3-3-70b-instruct",
    "api_key": "YOUR_API_KEY",
    "provider_endpoint": "https://us-south.ml.cloud.ibm.com",
    "model_params": {
        "project_id": "YOUR_PROJECT_ID"
    }
}'
```

#### Stores ####
```bash
curl -X GET http://localhost:5000/stores
```


#### Query ####
```bash
curl -X POST http://localhost:5000/query \
-H "Content-Type: application/json" \
-d '{
    "query": "Where was James Brown born?",
    "stores": ["wdqs"],
    "annotated": false
}'
```

#### Filter ####
```bash
curl -X POST http://localhost:5000/filter \
-H "Content-Type: application/json" \
-d '{
	"filters": [{
			"subject": { "iri": "http://www.wikidata.org/entity/Q378619"},
			"property": { "iri": "http://www.wikidata.org/entity/P31"}
		}],
	"stores": ["wdqs"],
	"annotated": false
}'
```
