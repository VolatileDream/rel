
def to_iter(o):
	if o is None:
		return []
	elif hasattr(o, "__iter__"):
		return o
	else:
		return [ o ]

import uuid

class Note(object):

	def __init__(self, notebook, vertex=None, content=None):
		self.notebook = notebook
		self.graph = notebook.graph

		if not vertex:
			self.vertex = self.graph.add_vertex()
			self.graph.vertex_properties[ Notebook.CONTENT_KEY ][ self.vertex ] = content
			self.graph.vertex_properties[ Notebook.ID_KEY ][ self.vertex ] = uuid.uuid4()
		else:
			# all the fields have been populated
			self.vertex = vertex

	@property
	def id(self):
		return self.graph.vertex_properties[ Notebook.ID_KEY ][ self.vertex ]

	@property
	def content(self):
		return self.graph.vertex_properties[ Notebook.CONTENT_KEY ][ self.vertex ]

	@content.setter
	def content_set(self, value):
		self.graph.vertex_properties[ Notebook.CONTENT_KEY ][ self.vertex ] = value


	def children(self, add=None, remove=None):
		add = to_iter(add)
		for child in add:
			self.notebook.create_edge(self, child)

		remove = to_iter( remove )
		for child in remove:
			self.notebook.remove_edge(self, child)

		return self.vertex.out_neighbours()


	def parents(self, add=None, remove=None):
		add = to_iter(add)
		for parent in add:
			self.notebook.create_edge(parent, self)

		remove = to_iter( remove )
		for parent in remove:
			self.notebook.remove_edge(parent, self)

		return self.vertex.in_neighbours()
	

from graph_tool.all import Graph, load_graph
import os


class Notebook(object):

	FORMAT = "graphml"

	ID_KEY = "id"
	CONTENT_KEY = "content"
	KEYS = [ ID_KEY, CONTENT_KEY ]

	def __init__(self, storage_file):

		self.stored = storage_file

		if os.path.exists(self.stored):
			self.graph = load_graph(self.stored, fmt=Notebook.FORMAT)
		else:
			self.graph = Graph()

			self.graph.vertex_properties[ Notebook.ID_KEY ] = self.graph.new_vertex_property("string")
			self.graph.vertex_properties[ Notebook.CONTENT_KEY ] = self.graph.new_vertex_property("string")


	def create_edge(self, parent, child):
		self.graph.add_edge( parent.vertex, child.vertex )


	def remove_edge(self, parent, child):
		edge = self.graph.edge(parent.vertex, child.vertex )
		self.graph.remove_edge( edge )


	def create_note(self, content=None):
		return Note( self, content=content )


	def remove_note(self, note=None, id=None):

		if note:
			id = note.id

		if not id:
			raise Error("ID required")

		number = -1
		for v in self.graph.vertices():
			if v.id == id:
				number = self.graph.vertex_index[ v ]
				break

		if number < 0:
			raise Error("Specified note doesn't exist")

		self.graph.remove_vertex( number, fast=True )


	def notes(self, predicate=None):

		for v in self.graph.vertices():
			n = Note(self, vertex=v)
			if not predicate or predicate(n):
				yield n


	def save(self):
		self.graph.save(self.stored, fmt=Notebook.FORMAT)


