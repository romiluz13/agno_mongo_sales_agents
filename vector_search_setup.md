# MongoDB Atlas Vector Search Setup


To enable full vector search capabilities, you need to create a Vector Search Index in MongoDB Atlas:

1. Go to MongoDB Atlas Dashboard
2. Navigate to your cluster
3. Click on "Search" tab
4. Click "Create Search Index"
5. Choose "Atlas Vector Search"
6. Use this configuration:

{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1024,
      "similarity": "cosine"
    }
  ]
}

7. Name the index: "vector_index"
8. Select collection: "vector_embeddings"
9. Click "Create Search Index"

This will enable full semantic search capabilities for your AI agents!
