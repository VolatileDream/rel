
def to_iter(o):
	if o is None:
		return []
	elif hasattr(o, "__iter__"):
		return o
	else:
		return [ o ]

import uuid

from py2neo import Node, Relationship
from datetime import datetime

class Note(object):

	label = "Note"
	SUMMARY_LENGTH = 140

	def __init__(self, notebook, node_or_content):
		self.notebook = notebook
		if type(node_or_content) is not Node:
			# graph libs can't handle uuid type
			self.node = Node(Note.label, content=node_or_content, created=datetime.utcnow(), id=str(uuid.uuid4()) )
		else:
			self.node = node_or_content


	@property
	def id(self):
		return self.node.properties[ "id" ]


	@property
	def created(self):
		return self.node.properties[ "created" ]


	@property
	def content(self):
		return self.node.properties[ "content" ]


	@content.setter
	def content_set(self, value):
		self.node.properties[ "content" ] = value


	@property
	# The short description of the item
	def short(self):
		try:
			newline_index = self.content.index("\n")
		except ValueError:
			newline_index = len(self.content)
		return self.content[ 0 : min(newline_index, Note.SUMMARY_LENGTH) ]


	def children(self, add=None, remove=None):
		add = to_iter(add)
		for child in add:
			self.notebook._create_edge(self, child)

		remove = to_iter( remove )
		for child in remove:
			self.notebook._remove_edge(self, child)

		for relation_child in self.node.match_outgoing(rel_type=RelatedNote.label):
			yield Note(self.notebook, relation_child.end_node)


	def parents(self, add=None, remove=None):
		add = to_iter(add)
		for parent in add:
			self.notebook._create_edge(parent, self)

		remove = to_iter( remove )
		for parent in remove:
			self.notebook._remove_edge(parent, self)

		for relation_parent in self.node.match_incoming(rel_type=RelatedNote.label):
			yield Note(self.notebook, relation_parent.start_node)

	def __repr__(self):
		return "{0}: {1}".format(self.id, self.short)


	def __hash__(self):
		return hash(self.id)


	def __eq__(self, other):
		if type(other) is Note:
			return self.id.__eq__(other.id)
		return False
	

class RelatedNote(object):

	label = "related_with"

	@staticmethod
	def wrap(relationship):
		return RelatedNote(relationship)

	def __init__(self, n0, n1=None):
		print(n1)
		if n1:
			self.rel = Relationship(n0.node, RelatedNote.label, n1.node)
		else:
			self.rel = n0


from py2neo import Graph
import os


class Notebook(object):

	def __init__(self, url="http://localhost:7474/db/data/"):
		self.g = Graph(url)


	def _create_edge(self, parent, child):
		r = RelatedNote(parent, child)
		self.g.create(r.rel)
		return r

	def _delete_edge(self, parent, child):
		edges = parent.node.matching_outgoing(rel_type=RelatedNote.label, other_node=child.node)
		self.g.delete(*edges)

	def create_note(self, content):
		n = Note( self, content )
		self.g.create(n.node)
		return n


	def remove_notes(self, *notes):
		self.g.delete(*notes)


	def notes(self, predicate=None):
		for v in self.g.find(Note.label):
			n = Note(self, v)
			if not predicate or predicate(n):
				yield n


	def export(self, file, fmt="dot"):
		self.g.save(file, fmt)

