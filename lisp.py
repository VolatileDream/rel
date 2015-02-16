from plyplus import Grammar, STransformer

NotebookQueryGrammar = Grammar("""

	@start	: expr				;
	expr	: '\(' func param* '\)'		;

	func	: '[^\(\)0-9" \t\n]+'		;
	number	: '[0-9]+(\.[0-9]+)?'		;
	string	: '"[^ \t\n]*"'			;
	@param	: string | number | expr	;

	WS: '[ \t\n]+' (%ignore) (%newline)	;

""")

class NotebookQueryParser(STransformer):

	def __init__(self, func_dict):
		self.func_dict = func_dict

	def expr(self, exp):
		return exp.tail[0]( *exp.tail[1:] )


	def func(self, exp):
		return self.func_dict[ exp.tail[0] ]


	def number(self, exp):
		try:
			return int(exp.tail[0])
		except ValueError:
			return float(exp.tail[0])


	def string(self, exp):
		# remove the quote characters
		return exp.tail[0][1:-1]


def parse(expr, func_dict):
	p = NotebookQueryParser(func_dict)
	ast = NotebookQueryGrammar.parse( expr )
	return p.transform( ast )

