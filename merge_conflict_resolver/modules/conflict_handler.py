from typing import List, Dict
import re
from .strategy_classifier import EnhancedStrategyClassifier
from .llm_resolver import LLMMergeResolver


class ConflictHandler:
    def __init__(self):
        self.classifier = EnhancedStrategyClassifier()
        self.llm_resolver = LLMMergeResolver()

    def parse_conflicts(self, file_content: str) -> List[Dict]:
        conflict_pattern = r"<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> (.+?)\n"
        matches = re.finditer(conflict_pattern, file_content, re.DOTALL)

        conflicts = []
        for match in matches:
            start_pos, end_pos = match.start(), match.end()
            context_before = file_content[max(0, start_pos - 300):start_pos].strip()
            context_after = file_content[end_pos:end_pos + 300].strip()

            conflicts.append({
                "a": match.group(1).strip(),
                "b": match.group(2).strip(),
                "branch": match.group(3).strip(),
                "context_before": context_before,
                "context_after": context_after,
            })

        return conflicts

    def resolve_conflict(self, conflict: Dict, file_content: str) -> str:
        prediction = self.classifier.predict_with_explanation(conflict)

        if prediction["strategy"] == "NEEDS_LLM" or prediction["confidence"] < 0.7:
            resolution = self.llm_resolver.resolve(conflict, file_content)
            return resolution.get("merged_code", "")

        strategy = prediction["strategy"]
        if strategy == "TAKE_A":
            return conflict["a"]
        elif strategy == "TAKE_B":
            return conflict["b"]
        elif strategy == "MERGE_BOTH":
            return f"{conflict['a']}\n\n{conflict['b']}"

        return self.llm_resolver.resolve(conflict, file_content).get("merged_code", "")

    def resolve_file(self, file_content: str) -> str:
        conflicts = self.parse_conflicts(file_content)
        if not conflicts:
            print("No conflicts detected.")
            return file_content

        resolved_content = file_content
        for conflict in conflicts:
            resolution = self.resolve_conflict(conflict, file_content)
            if resolution:
                conflict_pattern = (f"<<<<<<< HEAD\n{re.escape(conflict['a'])}\n=======\n{re.escape(conflict['b'])}\n"
                                    f">>>>>>> {re.escape(conflict['branch'])}\n")
                resolved_content = re.sub(conflict_pattern, resolution + "\n", resolved_content)

        return resolved_content

    def train_on_resolution(self, conflict: Dict, resolution: str, success: bool):
        if success:
            strategy = (
                "TAKE_A" if resolution == conflict["a"]
                else "TAKE_B" if resolution == conflict["b"]
                else "MERGE_BOTH" if resolution == f"{conflict['a']}\n\n{conflict['b']}"
                else "SMART_MERGE"
            )
            self.classifier.train([conflict], [strategy])
