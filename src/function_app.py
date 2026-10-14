import azure.functions as func

from handlers import documents, processor

# The `src/` directory is deployed as the Function App root, so imports are
# top-level (config, models, handlers.*, services.*).
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Register the blob trigger (processing pipeline) and the HTTP API.
processor.register(app)
documents.register(app)
