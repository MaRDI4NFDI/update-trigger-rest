# update-trigger-rest
A rest service to trigger updates on the portal, e.g. to get newest data from WikiData or to add a LLM generated article summary.

### Examples using curl

```shell
curl -X POST -H "Content-Type: application/json" -d '{
  "QID": "Q123",
  "caller": "MaRDI portal"
}' http://localhost:5000/generate_article_summary
```

