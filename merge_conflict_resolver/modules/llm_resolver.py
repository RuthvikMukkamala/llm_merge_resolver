from typing import Dict, List, Optional, TypedDict
import re
import openai
from openai.types.chat import ChatCompletion
from dotenv import load_dotenv
import os
import logging
from dataclasses import dataclass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()


class ConflictData(TypedDict):
    a: str
    b: str
    branch: str


class ResolutionResult(TypedDict):
    merged_code: Optional[str]
    explanation: Optional[str]
    risks: Optional[str]


@dataclass
class LLMResponse:
    merged_code: str
    explanation: str
    risks: str


class LLMMergeResolver:
    def __init__(self, model: str = "gpt-4"):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise EnvironmentError("OPENAI_API_KEY is not set in the .env file or environment.")

        openai.api_key = self.api_key
        self.model = model

    def _build_prompt(self, conflict: ConflictData, imports: List[str]) -> str:
        return f"""You are an expert programmer resolving a Git merge conflict. Your task is to merge the 
        conflicting versions while maintaining code quality and functionality.

        File context includes:
        - Relevant imports: {', '.join(imports)}

        Conflict:
        Version A:
        ```
        {conflict['a']}
        ```

        Version B:
        ```
        {conflict['b']}
        ```

        Instructions:
        1. Merge the two versions into a single valid solution.
        2. Maintain functionality and ensure code quality.
        3. If combining both versions is not possible, choose the best version.
        4. Provide an explanation of your decision.
        5. Highlight any risks or concerns in your resolution.

        Response format:
        MERGED_CODE:
        ```
        <your code here>
        ```

        EXPLANATION:
        <your explanation here>

        RISKS:
        <potential risks here>
        """

    def _parse_llm_response(self, content: str) -> LLMResponse:
        merged_code = re.search(r"MERGED_CODE:\n```(?:\w+\n)?(.*?)```", content, re.DOTALL)
        explanation = re.search(r"EXPLANATION:\n(.*?)\n\nRISKS:", content, re.DOTALL)
        risks = re.search(r"RISKS:\n(.*?)$", content, re.DOTALL)

        if not all([merged_code, explanation, risks]):
            raise ValueError("Invalid LLM response format")

        return LLMResponse(
            merged_code=merged_code.group(1).strip(),
            explanation=explanation.group(1).strip(),
            risks=risks.group(1).strip()
        )

    async def resolve_async(self, conflict: ConflictData, file_content: str) -> ResolutionResult:
        try:
            imports = analyze_imports(file_content)
            prompt = self._build_prompt(conflict, imports)

            response = await openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a code merge resolution assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

            logger.info(f"LLM Response received for conflict in branch: {conflict['branch']}")
            content = response.choices[0].message.content
            parsed_response = self._parse_llm_response(content)

            return {
                'merged_code': parsed_response.merged_code,
                'explanation': parsed_response.explanation,
                'risks': parsed_response.risks,
            }

        except Exception as e:
            logger.error(f"Error during merge resolution: {str(e)}", exc_info=True)
            return {
                'merged_code': None,
                'explanation': f"Error occurred during LLM call: {str(e)}",
                'risks': None,
            }

    def resolve(self, conflict: ConflictData, file_content: str) -> ResolutionResult:
        try:
            imports = analyze_imports(file_content)
            prompt = self._build_prompt(conflict, imports)

            response: ChatCompletion = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a code merge resolution assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

            logger.info(f"LLM Response received for conflict in branch: {conflict['branch']}")
            content = response.choices[0].message.content
            parsed_response = self._parse_llm_response(content)

            return {
                'merged_code': parsed_response.merged_code,
                'explanation': parsed_response.explanation,
                'risks': parsed_response.risks,
            }

        except Exception as e:
            logger.error(f"Error during merge resolution: {str(e)}", exc_info=True)
            return {
                'merged_code': None,
                'explanation': f"Error occurred during LLM call: {str(e)}",
                'risks': None,
            }


def analyze_imports(content: str) -> List[str]:
    import_pattern = r'^(?:from\s+\S+\s+)?import\s+\S+'
    return re.findall(import_pattern, content, re.MULTILINE)
