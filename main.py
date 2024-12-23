from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import git
import os

app = FastAPI()

# Path to your local git repository
REPO_PATH = "C:/Users/maheru/Desktop/MCodingTest/ProjectCompany/TESTGit"

class VersionCompareRequest(BaseModel):
    version1: str
    version2: str


@app.get("/")
def root():
    return {"message": "Welcome to the Git Version Comparison API"}


@app.post("/compare-versions/")
def compare_versions(request: VersionCompareRequest):
    if not os.path.exists(REPO_PATH):
        raise HTTPException(status_code=404, detail="Repository not found")

    try:
        # Initialize the repository
        repo = git.Repo(REPO_PATH)

        # Check if both versions exist in the repository
        if request.version1 not in repo.refs or request.version2 not in repo.refs:
            raise HTTPException(status_code=400, detail="One or both versions do not exist")

        # Get the commits for the versions
        commit1 = repo.commit(request.version1)
        commit2 = repo.commit(request.version2)

        # Compare the versions and get the list of modified files
        diff = commit1.diff(commit2, create_patch=True)

        modified_files_details = []

        for item in diff:
            file_details = {
                "file_path": item.a_path,
                "changes": []
            }

            if item.diff:  # Ensure there is a diff available
                diff_lines = item.diff.decode('utf-8').split('\n')

                current_line_number = 0
                added_lines = {}
                removed_lines = {}

                for line in diff_lines:
                    if line.startswith("@@"):
                        # Extract the line number info from the hunk header
                        hunk_info = line.split(" ")[1]
                        current_line_number = int(hunk_info.split(",")[0].replace("-", ""))
                    elif line.startswith("+") and not line.startswith("+++ "):
                        added_lines[current_line_number] = line[1:]  # Add line without '+'
                        current_line_number += 1
                    elif line.startswith("-") and not line.startswith("--- "):
                        removed_lines[current_line_number] = line[1:]  # Add line without '-'
                        current_line_number += 1

                # Combine changes into "modified," "added," or "removed"
                processed_lines = set()

                for line_num, content in added_lines.items():
                    if line_num in removed_lines:
                        file_details["changes"].append({
                            "line_number": line_num,
                            "type": "modified",
                            "old_content": removed_lines[line_num],
                            "new_content": content
                        })
                        processed_lines.add(line_num)
                    else:
                        file_details["changes"].append({
                            "line_number": line_num,
                            "type": "added",
                            "old_content": "None",
                            "new_content": content
                        })

                for line_num, content in removed_lines.items():
                    if line_num not in processed_lines:
                        file_details["changes"].append({
                            "line_number": line_num,
                            "type": "removed",
                            "old_content": content,
                            "new_content": "None"
                        })

            if file_details["changes"]:  # Add only if there are changes
                modified_files_details.append(file_details)

        return {
            "version1": request.version1,
            "version2": request.version2,
            "modified_files_count": len(modified_files_details),
            "modified_files_details": modified_files_details
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")




