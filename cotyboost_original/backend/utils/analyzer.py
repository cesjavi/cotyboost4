import os

def analyze_project(project_path):
    file_count = 0
    total_lines = 0
    total_size_mb = 0.0

    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith((".py", ".js", ".ts", ".cpp", ".c", ".java", ".cs", ".go"," .html", ".css","vue", ".php", ".rb", ".swift", ".kt")):
                file_count += 1
                try:
                    with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        total_lines += len(lines)
                except Exception:
                    pass
            total_size_mb += os.path.getsize(os.path.join(root, file)) / (1024 * 1024)

    recommendation = "qlora" if total_lines > 10000 or total_size_mb > 50 else "lora"
    model = "codellama/CodeLlama-7b-hf" if recommendation == "qlora" else "Salesforce/codegen-2B-mono"

    return {
        "file_count": file_count,
        "total_lines": total_lines,
        "total_size_mb": round(total_size_mb, 2),
        "recommendation": recommendation,
        "suggested_model": model
    }
