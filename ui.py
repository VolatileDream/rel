from graph import Graph, Node, Edge

import click

import os

options = {}

def get_graph():
	return Graph(options["database"])


@click.group()
@click.argument("database")
# help="URI for sqlite3 database")
def nb_ui(**kvargs):
	options.update(kvargs)


@nb_ui.command("add")
@click.argument("content", required=False)
@click.option("-p", "--parent", multiple=True)
@click.option("-c", "--child", multiple=True)
def add_note(content, parent, child):

	if content is None:
		content = "/dev/stdin"

	if os.path.exists(content):
		with open(content) as f:
			content = "".join( f.readlines() )

	graph = get_graph()
	node = graph.create_node(unicode(content))

	if parent or child:
		update_relationships(False, parent, child, [note.id])

	graph.commit()
	print(node.id)


@nb_ui.command("remove")
@click.argument("id")
def remove_node(id):

	graph = get_graph()
	node = graph.node(id)
	graph.remove_node(node)
	graph.commit()


import query, lisp

@nb_ui.command("list")
@click.option("-t", "--template", default="{id} := {content}")
@click.argument("filter", required=False)
def list_notes(template, filter):

	graph = get_graph()

	if filter:
		# use plyplus to construct the filter/selection function
		traversal = lisp.parse(filter, query.get_context_functions())
	else:
		# as an optional argument, we must construct a passthrough
		traversal = lambda x : x

	for node in traversal( set(graph.nodes()) ):
		print( template.format( id=node.id, content=node.content, short=node.short ) )


def update_relationships(remove, parent, child, notes):

	def matching_id(id_list):
		def in_list(note):
			return note.id in id_list
		return in_list

	graph = get_graph()

	parents = list( graph.notes( matching_id(parent) ) )
	children = list( graph.notes( matching_id(child) ) )

	for node in graph.nodes( matching_id(notes) ):
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
@click.argument("notes", nargs=-1)
def relations(remove, parent, child, notes):
	update_relationships(remove, parent, child, notes)


if __name__ == "__main__":
	nb_ui()

