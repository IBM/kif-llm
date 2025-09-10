import ast

from kifqa.parsers.abc import PromptOutputParser


class PythonTriplePatternParser(PromptOutputParser):

    def parse(self, text: str) -> list[list[tuple[str, str, str]]]:
        try:
            return ast.literal_eval(text)
        except Exception as e:
            raise ValueError(
                f"""Error in interpreting LLM response as a Python object: {e.__str__()}
                LLM response: {text})""")
