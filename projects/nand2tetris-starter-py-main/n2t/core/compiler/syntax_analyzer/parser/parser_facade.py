from typing import Iterable

from n2t.core.compiler.syntax_analyzer.parser.jack_xml_generator import JackXmlCompiler
from n2t.core.compiler.syntax_analyzer.tokenizer.tokenizer_facade import JackTokenizer
from n2t.infra.io import FileFormat


class jackXmlParser:
    def get_file_format(self) -> FileFormat:
        return FileFormat.xml

    def parse(self, tokenizer: JackTokenizer) -> Iterable[str]:
        return list[str](JackXmlCompiler(tokenizer).compile_class())
