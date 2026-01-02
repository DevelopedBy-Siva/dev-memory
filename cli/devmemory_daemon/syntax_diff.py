from pathlib import Path
from typing import Dict, List, Optional
import difflib

try:
    from tree_sitter import Language, Parser
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjs

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


class SyntaxAwareDiff:

    def __init__(self):
        if not TREE_SITTER_AVAILABLE:
            self.parsers = {}
            return

        try:
            py_lang = Language(tspython.language())
            js_lang = Language(tsjs.language())
        except TypeError:
            py_lang = tspython.language()
            js_lang = tsjs.language()

        self.parsers = {
            "py": Parser(py_lang),
            "js": Parser(js_lang),
            "jsx": Parser(js_lang),
            "ts": Parser(js_lang),
            "tsx": Parser(js_lang),
        }

    def extract_functions(self, code: str, file_type: str) -> List[Dict]:
        if file_type not in self.parsers:
            return []

        try:
            tree = self.parsers[file_type].parse(bytes(code, "utf8"))
            functions = []

            def traverse(node):
                if node.type in [
                    "function_definition",
                    "async_function_definition",
                    "function_declaration",
                    "method_definition",
                ]:
                    func_name = self._get_function_name(node, code)
                    functions.append(
                        {
                            "name": func_name,
                            "start": node.start_byte,
                            "end": node.end_byte,
                            "code": code[node.start_byte : node.end_byte],
                            "type": node.type,
                        }
                    )

                for child in node.children:
                    traverse(child)

            traverse(tree.root_node)
            return functions

        except Exception as e:
            return []

    def _get_function_name(self, node, code: str) -> str:
        """Extract function name from AST node"""
        for child in node.children:
            if child.type == "identifier":
                return code[child.start_byte : child.end_byte]
        return "<anonymous>"

    def compute_semantic_diff(
        self, old_code: str, new_code: str, file_type: str
    ) -> Dict:
        if not TREE_SITTER_AVAILABLE or file_type not in self.parsers:
            return self._fallback_line_diff(old_code, new_code)

        old_funcs = {f["name"]: f for f in self.extract_functions(old_code, file_type)}
        new_funcs = {f["name"]: f for f in self.extract_functions(new_code, file_type)}

        added = [name for name in new_funcs if name not in old_funcs]
        deleted = [name for name in old_funcs if name not in new_funcs]

        modified = []
        for name in new_funcs:
            if name in old_funcs:
                if new_funcs[name]["code"] != old_funcs[name]["code"]:
                    modified.append(
                        {
                            "name": name,
                            "old": old_funcs[name]["code"],
                            "new": new_funcs[name]["code"],
                        }
                    )

        storage_size = sum(
            len(f["code"]) for f in new_funcs.values() if f["name"] in added
        )
        storage_size += sum(len(m["new"]) for m in modified)

        return {
            "mode": "semantic",
            "functions_added": added,
            "functions_deleted": deleted,
            "functions_modified": modified,
            "storage_size": storage_size,
            "original_size": len(old_code) + len(new_code),
            "savings_percent": self._calculate_savings(
                storage_size, len(old_code) + len(new_code)
            ),
        }

    def _fallback_line_diff(self, old_code: str, new_code: str) -> Dict:
        """Simple line-based diff when tree-sitter not available"""
        diff = list(
            difflib.unified_diff(
                old_code.splitlines(keepends=True),
                new_code.splitlines(keepends=True),
                lineterm="",
            )
        )

        return {
            "mode": "line_based",
            "diff": "".join(diff),
            "storage_size": len("".join(diff)),
            "original_size": len(old_code) + len(new_code),
        }

    def _calculate_savings(self, semantic_size: int, original_size: int) -> float:
        """Calculate percentage savings"""
        if original_size == 0:
            return 0.0
        return ((original_size - semantic_size) / original_size) * 100


syntax_diff = SyntaxAwareDiff()


def analyze_patch_with_syntax(patch_text: str) -> Dict:
    stats = {
        "files_changed": 0,
        "functions_added": [],
        "functions_modified": [],
        "functions_deleted": [],
        "total_savings_percent": 0.0,
    }

    current_file = None
    old_content = []
    new_content = []

    for line in patch_text.split("\n"):
        if line.startswith("diff --git"):
            if current_file:
                file_ext = Path(current_file).suffix[1:]
                if file_ext in ["py", "js", "jsx", "ts", "tsx"]:
                    result = syntax_diff.compute_semantic_diff(
                        "\n".join(old_content), "\n".join(new_content), file_ext
                    )

                    if result.get("mode") == "semantic":
                        stats["functions_added"].extend(result["functions_added"])
                        stats["functions_modified"].extend(
                            [f["name"] for f in result["functions_modified"]]
                        )
                        stats["functions_deleted"].extend(result["functions_deleted"])
                        stats["total_savings_percent"] += result.get(
                            "savings_percent", 0
                        )

            parts = line.split()
            if len(parts) >= 4:
                current_file = parts[3].replace("b/", "")
                stats["files_changed"] += 1
                old_content = []
                new_content = []

        elif line.startswith("---") or line.startswith("+++"):
            continue
        elif line.startswith("-") and not line.startswith("---"):
            old_content.append(line[1:])
        elif line.startswith("+") and not line.startswith("+++"):
            new_content.append(line[1:])
        else:
            old_content.append(line)
            new_content.append(line)

    if stats["files_changed"] > 0:
        stats["total_savings_percent"] /= stats["files_changed"]

    return stats
