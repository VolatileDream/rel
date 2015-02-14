from notes import Notebook

import click

import os

def get_book():
	return Notebook("/tmp/graph")

@click.group()
def nb_ui():
	pass

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
	book.save()

	print(note.id)


@nb_ui.command("remove")
@click.argument("id")
def remove_note(id):

	book = get_book()
	book.remove_note(id)
	book.save()


@nb_ui.command("list")
@click.option("-t", "--template", default="{0} := {1}")
@click.argument("filter", required=False)
def list_notes(template, filter):

	book = get_book()

	# use plyplus to construct the filter/selection function

	for note in book.notes():
		print( template.format( note.id, note.content ) )


@nb_ui.command("relations")
@click.option("--remove", is_flag=True)
@click.option("-p", "--parent", multiple=True)
@click.option("-c", "--child", multiple=True)
@click.argument("notes", nargs=-1)
def update_relationshisp(remove, parent, child, notes):

	print( notes )
	print( parent )
	print( child )

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


if __name__ == "__main__":
	nb_ui()

