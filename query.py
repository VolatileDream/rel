func_table = {}

def get_functions():
	return dict(func_table) # return non-mutable copy


def expose(func, table=None):
	return expose2(func.__name__, func, table=table)


def expose2(name, function, table=None):
	if not table:
		func_table[ name ] = function
	else:
		table[name] = function
	return function


def expose_as(name, table=None):
	def wrap(func):
		return expose2( name, func, table=table )
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
def for_all(func):
	return lambda nodes: set([ n for n in nodes if func(n) ])


@expose_as("print")
def p(arg):
	def other_p(nodes):
		result = arg(nodes)
		print(result)
		return result
	return other_p

import re

@expose_as("match")
def regex_match(regex):
	regex = re.compile(regex)
	return for_all( lambda note: regex.match(note.content) )


@expose_as("id=")
def id_eq(val):
	return for_all( lambda note: note.id is val )


@expose_as("id~")
def id_like(val):
	return for_all( lambda note: val in note.id )

@expose_as("~")
def like(val):
	return for_all( lambda note: val in note.content )


@expose_as("not")
def negate(cond):
	return lambda notes: notes.difference( cond(notes) )


## Logic stuff


def logic(default, reduction, constraints=None):
	""" provide a default value for reduction, and extra constraints that must be met """
	def logic(*conds):
		def check_logic(note):
			results = map( lambda cond: cond(note), conds )
			reduced = reduce( reduction, results, default )
			if not constraints or constraints(results):
				return reduced
			return False
		return check_logic
	return logic


@expose_as("and")
def intersect(*conds):

	def i(notes):
		result_sets = map( lambda cond: cond(notes), conds )
		reduced = reduce( lambda x, y: x.intersection(y), result_sets, notes )
		return reduced

	return i

@expose_as("or")
def union(*conds):
	def u(notes):
		result_sets = map( lambda cond: cond(notes), conds )
		reduced = reduce( lambda x, y: x.union(y), result_sets, set() )
		return reduced

	return u

## Here be dragons


def iter_check(item_gen):
	""" given a way to generate new items (item_gen), and an item to
		generate from (note_gens), generate more notes. """
	def top(*note_gens):
		def check(notes):
			result_notes = union(*note_gens)(notes)
			new_items = map( item_gen, result_notes )
			result = reduce( lambda x, y: x.union(y), new_items, set() )
			return result
		return check
	return top


@expose_as("parent")
@iter_check
def parent(note):
	return set(note.parents())

@expose_as("child")
@iter_check
def child(note):
	return set(note.children())

@expose_as("related")
@iter_check
def related(note):
	return set(note.children()).union( set(note.parents()) )


### And now for magic...

def get_context_functions():

	ctx_funcs = dict(get_functions())
	context = {}

	def init_name(name):
		try:
			context[name]
		except KeyError:
			context[name] = set()

	@expose_as("?", table=ctx_funcs)
	def aggregate(name, *conds):
		init_name(name)
		def do_ag(notes):
			result = union(*conds)( notes )
			context[name].update( result )
			return result
		return do_ag

	@expose_as("!", table=ctx_funcs)
	def ret(name, *conds):
		init_name(name)
		def do_ret(notes):
			result = union(*conds)( notes )
			return result.union( context[name] )
		return do_ret


	return ctx_funcs
