from fastapi import FastAPI, UploadFile, File, Body, HTTPException
from fastapi.responses import JSONResponse
from modules.conflict_handler import ConflictHandler
import logging

# Initialize FastAPI and configure logging
app = FastAPI()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize ConflictHandler
conflict_handler = ConflictHandler()


@app.post("/merge_resolver")
async def resolve_conflicts(file: UploadFile = File(None), content: str = Body(None)):
    """
    Resolves merge conflicts in the uploaded file.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded. Please upload a file!")

    try:
        # Read the file content
        content = await file.read()
        content = content.decode("utf-8")

        # Parse conflicts using the ConflictHandler
        conflicts = conflict_handler.parse_conflicts(content)
        if not conflicts:
            raise HTTPException(status_code=400, detail="No conflicts detected in the file.")

        resolved_content = content
        unresolved_conflicts = []

        # Resolve each conflict
        for conflict in conflicts:
            try:
                resolution = conflict_handler.resolve_conflict(conflict, resolved_content)
                if not resolution:
                    raise ValueError("No valid resolution returned for the conflict.")
                logging.info(f"Conflict resolved successfully for branch {conflict.get('branch', 'unknown')}.")
            except Exception as e:
                logging.error(f"Error resolving conflict: {repr(conflict)}. Error: {e}")
                unresolved_conflicts.append({"conflict": conflict, "error": str(e)})
                continue

            # Replace the conflict block with the resolution
            conflict_pattern = (
                f"<<<<<<< HEAD\n{conflict['a']}\n=======\n{conflict['b']}\n>>>>>>> {conflict['branch']}"
            )
            resolved_content = resolved_content.replace(conflict_pattern, resolution or "")

        response = {
            "resolved_content": resolved_content,
            "unresolved_conflicts": unresolved_conflicts,
        }
        return JSONResponse(response)

    except Exception as e:
        logging.error(f"Unexpected error during conflict resolution: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during conflict resolution.")


@app.get("/")
def health_check():
    return {"status": "running", "message": "Merge Conflict Resolver API is active!"}
