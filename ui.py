from notes import Notebook

import click

import os

options = { "neo4j" : "http://localhost:7474/db/data/" }

def get_book():
	return Notebook(options["neo4j"])

@click.group()
@click.option("--neo4j")
def nb_ui(**kvargs):
	options.update(kvargs)

@nb_ui.command("add")
@click.argument("content", required=False)
def add_note(content):

	if content is None:
		content = "/dev/stdin"

	if os.path.exists(content):
		with open(content) as f:
			content = "".join( f.readlines() )

	book = get_book()
	note = book.create_note(content)

	print(note.id)


@nb_ui.command("remove")
@click.argument("id")
def remove_note(id):

	book = get_book()
	book.remove_note(id)


import query, lisp

@nb_ui.command("list")
@click.option("-t", "--template", default="{id} := {content}")
@click.argument("filter", required=False)
def list_notes(template, filter):

	book = get_book()

	if filter:
		# use plyplus to construct the filter/selection function
		traversal = lisp.parse(filter, query.get_context_functions())
	else:
		# as an optional argument, we must construct a passthrough
		traversal = lambda x : x

	for note in traversal( set(book.notes()) ):
		print( template.format( id=note.id, content=note.content, short=note.short ) )


@nb_ui.command("relations")
@click.option("--remove", is_flag=True)
@click.option("-p", "--parent", multiple=True)
@click.option("-c", "--child", multiple=True)
@click.argument("notes", nargs=-1)
def update_relationshisp(remove, parent, child, notes):

	def matching_id(id_list):
		def in_list(note):
			return note.id in id_list
		return in_list

	book = get_book()

	parents = list( book.notes( matching_id(parent) ) )
	children = list( book.notes( matching_id(child) ) )

	for note in book.notes( matching_id(notes) ):
		if remove:
			note.parents(remove=parents)
			note.children(remove=children)
		else:
			note.parents(add=parents)
			note.children(add=children)



@nb_ui.command("export")
@click.option("-f", "--format", default="dot", type=click.Choice(["dot", "gml", "gt", "graphml"]))
@click.argument("file", type=click.Path(exists=False, writable=True, dir_okay=False), required=False)
def export_graph(format, file=None):

	book = get_book()

	if not file:
		file = "/dev/stdout"

	book.export(file, format)


if __name__ == "__main__":
	nb_ui()

