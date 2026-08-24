from services import github_pr_service, qa_context_service


def build_analysis_context(pr_number):
    pull_request = github_pr_service.get_pull_request(pr_number)
    changed_files = github_pr_service.get_pull_request_files(pr_number)
    qa_context = qa_context_service.build_qa_context()

    change_summary = {
        "files_changed": len(changed_files),
        "additions": sum(file["additions"] for file in changed_files),
        "deletions": sum(file["deletions"] for file in changed_files),
        "total_changes": sum(file["total_changes"] for file in changed_files),
    }

    return {
        "pull_request": pull_request,
        "change_summary": change_summary,
        "changed_files": changed_files,
        "qa_context": qa_context,
    }
