from plyplus import Grammar, STransformer

NotebookQueryGrammar = Grammar("""

	@start	: expr				;
	expr	: '\(' func param* '\)'		;

	func	: '[a-zA-Z_/\*\+\-]+'		;
	number	: '[0-9]+(\.[0-9]+)?'		;
	string	: '"[^ \t\n]*"'			;
	@param	: string | number | expr	;

	WS: '[ \t\n]+' (%ignore) (%newline)	;

""")

func_table = {}
def expose(func):
	return expose(func.__name__, func)

def expose(name, function):
	func_table[ name ] = function
	return function

# Expose some math
expose("+", lambda *x : reduce( lambda x, y: x + y, x, 0 ) )
expose("*", lambda *x : reduce( lambda x, y: x * y, x, 1 ) )
expose("/", lambda x, y : x / y )
expose("//", lambda x, y : x // y )

def subtract(*args):
	if len(args) is 1:
		return -args[0]
	elif len(args) is 0:
		return 0
	else:
		return reduce( lambda x, y: x - y, args[1:], args[0] )

expose("-", subtract)

class NotebookQueryParser(STransformer):

	def expr(self, exp):
		return exp.tail[0]( *exp.tail[1:] )


	def func(self, exp):
		return func_table[ exp.tail[0] ]


	def number(self, exp):
		try:
			return int(exp.tail[0])
		except ValueError:
			return float(exp.tail[0])


	def string(self, exp):
		# remove the quote characters
		return exp.tail[0][1:-1]


def parse(expr):
	p = NotebookQueryParser()
	ast = NotebookQueryGrammar.parse( expr )
	print(ast)
	return p.transform( ast )
