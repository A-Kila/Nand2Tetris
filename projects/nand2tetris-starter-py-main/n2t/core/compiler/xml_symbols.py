class XMLSymbols:
    symbols = {
        "<": "&lt;",
        ">": "&gt;",
        '"': "&qout;",
        "&": "&amp;",
    }

    @classmethod
    def get_xml_symbol(cls, symbol: str) -> str:
        return cls.symbols.get(symbol, symbol)
