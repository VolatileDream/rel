from graph import Graph, Node, Edge

import click

import os
import sys

options = { "graph" : None }

def get_graph():
	# return the same object every time
	if not options["graph"]:
		options["graph"] = Graph(options["database"])
	return options["graph"]


@click.group()
@click.argument("database")
# help="URI for sqlite3 database")
def nb_ui(**kvargs):
	options.update(kvargs)


@nb_ui.command("init", short_help="create a new graph")
def init():
	g = get_graph()
	g.commit();


@nb_ui.command("add", short_help="create a new node")
@click.argument("content", required=False)
def add_node(content):
	"""Creates a node and accepts it's content from either the command line,
	or stdin if no command line content was given. Prints the nodes id to stdout.
	"""

	if content is None:
		content = "/dev/stdin"

	if os.path.exists(content):
		with open(content) as f:
			content = "".join( f.readlines() )

	graph = get_graph()
	node = graph.create_node(unicode(content))

	graph.commit()

	print(node.id)


@nb_ui.command("remove", short_help="remove node with id ID from the graph")
@click.argument("id")
def remove_node(id):

	graph = get_graph()
	node = graph.node(int(id))
	graph.remove_nodes(node)
	graph.commit()


def edit_content(content):
	from tempfile import NamedTemporaryFile

	with NamedTemporaryFile("w+b") as temp:

		# write node content to file
		temp.write(content)
		temp.flush()

		# get the user to edit it, exit of 0 is success, anything else isn't
		rc = os.spawnlp(os.P_WAIT, "sensible-editor", "sensible-editor", temp.name)

		# they aborted editing, return old content
		if rc != 0:
			return content

		temp.seek(0) # go to beginning of file

		return "".join( temp.readlines() )


@nb_ui.command("edit", short_help="edit node ID's contents")
@click.option("-s", "--stdin", is_flag=True, help="take new contents from stdin")
@click.argument("id")
def edit_node(id, stdin):
	"""Edit a nodes content using 'sensible-editor', or replaces a nodes
	content with content from stdin.
	"""

	graph = get_graph()

	node = graph.node(int(id))
	if not node:
		sys.stderr.write("Couldn't find node with id: %s\n" % str(id) )
		return 1

	if not stdin:
		new_content = edit_content(node.content)
	else:
		with sys.stdin as f:
			new_content = "".join( f.readlines() )


	node.content = unicode(new_content)

	graph.commit()


@nb_ui.command("export", short_help="output the graph in dot format")
def data_export():
	"""Outputs a formatted dot graph to stdout, uses node short description
	as labels."""

	graph = get_graph()

	print("digraph g {")

	for node in graph.nodes():
		print('\t{id} [label="{short}"]'.format(id=node.id, short=node.short))
		for out_edge in graph.edges( Edge.head_id == node.id ):
			print('\t\t{parent} -> {child} [label="{label}"]'.format(parent=node.id, child=out_edge.tail_id, label=out_edge.label))

	print("}")


import query, lisp

@nb_ui.command("list", short_help="query the graph")
@click.option("-t", "--template", default="{id} := {content}", help="output template for nodes")
@click.argument("filter", required=False)
def list_nodes(template, filter):
	"""Query the graph with FILTER, and output nodes formated as TEMPLATE.

	Template is an arbitrary string without '{' or '}', it exposes the values
	for the nodes id, content, short content, and time created. These are
	represented as '{id}', '{content}', '{short}', and '{created}'.

	[TODO: Filter Format]
	"""

	graph = get_graph()

	if filter:
		# use plyplus to construct the filter/selection function
		traversal = lisp.parse(filter, query.get_context_functions())
	else:
		# as an optional argument, we must construct a passthrough
		traversal = lambda x : x

	for node in traversal( set(graph.nodes()) ):
		print( template.format( id=node.id, content=node.content, short=node.short, created=node.created ) )


def update_relationships(remove, parent, child, nodes, label):

	if not label:
		label = u"related"

	graph = get_graph()

	# make sure they're ints, we might be getting these from the cli
	nodes = [ int(x) for x in nodes ]
	parent = [ int(x) for x in parent ]
	child = [ int(x) for x in child ]

	parents = list( graph.nodes( Node.id.is_in(parent) ) )
	children = list( graph.nodes( Node.id.is_in(child) ) )

	for node in graph.nodes( Node.id.is_in(nodes) ):
		if remove:
			node.update_parents(remove=parents, label=label)
			node.update_children(remove=children, label=label)
		else:
			node.update_parents(add=parents, label=label)
			node.update_children(add=children, label=label)

	graph.commit()


@nb_ui.command("related", short_help="edit the edges for a set of nodes")
@click.option("--remove", is_flag=True, help="remove edges instead of adding them")
@click.option("-p", "--parent", multiple=True, help="incoming edges from this node (multiple)")
@click.option("-c", "--child", multiple=True, help="outgoing edges to this node (multiple)")
@click.option("-l", "--label", default=None, help="the label for the edges")
@click.argument("nodes", nargs=-1)
def relations(remove, parent, child, label, nodes):
	"""Modifies the edges attached to a set of nodes, adding or removing
	incoming and outgoing edges specified with --parent and --child
	respectively. The label on the edges is specified by --label, but
	defaults to 'related'.
	"""
	update_relationships(remove, parent, child, nodes, label)


@nb_ui.command("edge", short_help="edit the edges for a pair of nodes")
@click.option("--remove", is_flag=True, help="remove edges instead of adding them")
@click.option("-l", "--label", default=None, help="the label for the edges")
@click.argument("parent")
@click.argument("child")
def single_edge(remove, parent, child, label):

	update_relationships(remove, [ parent ], [], [ child ], label)


if __name__ == "__main__":
	nb_ui()

