# Vector configuration creation retirement

New pgvector configuration registration is retired. Existing
`project.vector.search()` and `project.vector.similar_to()` integrations remain
available for configurations that were registered previously.

For new vector setup, use `project.context.create_collection()` with a native
`pgcontext.vector` column. The server reports
`VECTOR_CREATION_RETIRED` when an older client calls the retired
`POST /v1/vector/configurations` endpoint.
