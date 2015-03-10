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


@nb_ui.command("init")
def init():
	g = get_graph()
	g.commit();


@nb_ui.command("add")
@click.argument("content", required=False)
@click.option("-p", "--parent", multiple=True)
@click.option("-c", "--child", multiple=True)
def add_node(content, parent, child):

	if content is None:
		content = "/dev/stdin"

	if os.path.exists(content):
		with open(content) as f:
			content = "".join( f.readlines() )

	graph = get_graph()
	node = graph.create_node(unicode(content))

	graph.commit() # otherwise node.id == None

	if parent or child:
		update_relationships(False, parent, child, [node.id])

	graph.commit()
	print(node.id)


@nb_ui.command("remove")
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


@nb_ui.command("edit")
@click.argument("id")
def edit_node(id):

	graph = get_graph()

	node = graph.node(int(id))
	if not node:
		sys.stderr.write("Couldn't find node with id: %s\n" % str(id) )
		return 1

	new_content = edit_content(node.content)

	node.content = unicode(new_content)

	graph.commit()


@nb_ui.command("export")
def data_export():

	graph = get_graph()

	print("digraph g {")

	for node in graph.nodes():
		print('\t{id} [label="{short}"]'.format(id=node.id, short=node.short))
		for child in graph.nodes( Node.id == Edge.tail_id, Edge.head_id == node.id ):
			print("\t{parent} -> {child}".format(parent=node.id, child=child.id))

	print("}")


import query, lisp

@nb_ui.command("list")
@click.option("-t", "--template", default="{id} := {content}")
@click.argument("filter", required=False)
def list_nodes(template, filter):

	graph = get_graph()

	if filter:
		# use plyplus to construct the filter/selection function
		traversal = lisp.parse(filter, query.get_context_functions())
	else:
		# as an optional argument, we must construct a passthrough
		traversal = lambda x : x

	for node in traversal( set(graph.nodes()) ):
		print( template.format( id=node.id, content=node.content, short=node.short, created=node.created ) )


def update_relationships(remove, parent, child, nodes):

	graph = get_graph()

	# make sure they're ints, we might be getting these from the cli
	nodes = [ int(x) for x in nodes ]
	parent = [ int(x) for x in parent ]
	child = [ int(x) for x in child ]

	parents = list( graph.nodes( Node.id.is_in(parent) ) )
	children = list( graph.nodes( Node.id.is_in(child) ) )

	for node in graph.nodes( Node.id.is_in(nodes) ):
		if remove:
			node.update_parents(remove=parents)
			node.update_children(remove=children)
		else:
			node.update_parents(add=parents)
			node.update_children(add=children)

	graph.commit()


@nb_ui.command("related")
@click.option("--remove", is_flag=True)
@click.option("-p", "--parent", multiple=True)
@click.option("-c", "--child", multiple=True)
@click.argument("nodes", nargs=-1)
def relations(remove, parent, child, nodes):
	update_relationships(remove, parent, child, nodes)


if __name__ == "__main__":
	nb_ui()

