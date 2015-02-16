func_table = {}

def get_functions():
	return dict(func_table) # return non-mutable copy


def expose(func):
	return expose2(func.__name__, func)


def expose2(name, function):
	func_table[ name ] = function
	return function


def expose_as(name):
	def wrap(func):
		return expose2( name, func )
	return wrap


# Expose some math
expose2("+", lambda *x : reduce( lambda x, y: x + y, x, 0 ) )
expose2("*", lambda *x : reduce( lambda x, y: x * y, x, 1 ) )
expose2("/", lambda x, y : x / y )
expose2("//", lambda x, y : x // y )

@expose_as("-")
def subtract(*args):
	if len(args) is 1:
		return -args[0]
	elif len(args) is 0:
		return 0
	else:
		return reduce( lambda x, y: x - y, args[1:], args[0] )


# The things that are important to expose

@expose
def id_eq(val):
	return lambda note: note.id is val

@expose
def id_like(val):
	return lambda note: val in note.id

@expose
def like(val):
	return lambda note: val in note.content

def check(maybe_cond):
	def c(note):
		if callable(maybe_cond):
			return maybe_cond(note)
		else:
			# yay, truthy/falsy -> truth/false conversion
			return not not maybe_cond
	return c


@expose_as("not")
def negate(cond):
	cond = check(cond)
	return lambda note: not cond(note)


## Logic stuff


def logic(default, reduction, constraints=None):
	""" provide a default value for reduction, and extra constraints that must be met """
	def logic(*conds):
		conds = map( check, conds )
		def check_logic(note):
			results = map( lambda cond: cond(note), conds )
			reduced = reduce( reduction, results, default )
			if not constraints or constraints(results):
				return reduced
			return False
		return check_logic
	return logic


expose_as("all")(
	logic(True,
		lambda x, y: x and y,
		lambda res: len(res) > 0) )


expose_as("and")(
	logic(True, lambda x, y: x and y) )


expose_as("one")(
	logic(False,
		lambda x, y: x or y,
		lambda res: len(res) > 0) )


expose_as("or")(
	logic(False, lambda x, y: x or y ) )

## Here be dragons
def iter_check(item_gen, join_cond):
	def top(*conds):
		check_and = func_table['and'](*conds)
		def check(note):
			conds = map( lambda p: lambda f: f(p), item_gen(note) )
			return join_cond( conds )( check_and )
		return check
	return top


expose_as("parent+")(
	iter_check( lambda note: note.parents(), func_table['one'] ) )

expose_as("parent")(
	iter_check( lambda note: note.parents(), func_table['or'] ) )

expose_as("child+")(
	iter_check( lambda note: note.children(), func_table['one'] ) )

expose_as("child")(
	iter_check( lambda note: note.children(), func_table['or'] ) )

### And now for magic...

def use_context_functions():
	context = {}

	def init_name(name):
		try:
			context[name]
		except KeyError:
			context[name] = []

	@expose_as("?")
	def aggregate(name, *conds):
		init_name(name)
		def do_ag(note):
			result = func_table['and'](*conds)( note )
			if result:
				context[name].append( note )
			return result
		return do_ag


	return context
