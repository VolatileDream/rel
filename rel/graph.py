def to_iter(o):
	if o is None:
		return []
	elif hasattr(o, "__iter__"):
		return o
	else:
		return [ o ]


from storm.locals import *
from datetime import datetime

class Node(object):

	SUMMARY_LENGTH = 140

	__table_decl__ = "CREATE TABLE node (" \
			 "id INTEGER, content VARCHAR, created DATETIME," \
			 "PRIMARY KEY (id) )"

	# storm attributes
	__storm_table__ = 'node'
	id = Int(primary=True)
	content = Unicode()
	created = DateTime(default_factory=lambda: datetime.utcnow())

	def __init__(self, content, created=None):
		self.content = content
		if created:
			self.created = created
		#else:
		#	self.created = datetime.utcnow()


	@property
	# The short description of the item
	def short(self):
		try:
			newline_index = self.content.index("\n")
		except ValueError:
			newline_index = len(self.content)
		return self.content[ 0 : min(newline_index, Node.SUMMARY_LENGTH) ]


	@staticmethod
	def _create_edge(storm, parent, child):
		r = Edge(parent.id, child.id)
		storm.add(r)
		return r


	@staticmethod
	def _delete_edge(storm, parent, child):
		edge = storm.find(Edge, Edge.head_id == parent.id, Edge.tail_id == child.id).one()
		storm.remove(edge)

	def update_children(self, add=None, remove=None):
		store = Store.of(self)
		add = to_iter(add)
		for child in add:
			Node._create_edge(store, self, child)

		remove = to_iter(remove)
		for child in remove:
			Node._delete_edge(store, self, child)


	def update_parents(self, add=None, remove=None):
		store = Store.of(self)
		add = to_iter(add)
		for parent in add:
			Node._create_edge(store, parent, self)

		remove = to_iter(remove)
		for parent in remove:
			Node._delete_edge(store, parent, self)


	def children(self):
		store = Store.of(self)
		return store.find(Node, Edge.head == self.id, Edge.tail == Node.id)


	def parents(self):
		store = Store.of(self)
		return store.find(Node, Edge.tail == self.id, Edge.head == Node.id)


	def __repr__(self):
		return "{0}: {1}".format(self.id, self.short)


	def __hash__(self):
		return hash(self.id)


	def __eq__(self, other):
		if type(other) is Note:
			return self.id.__eq__(other.id)
		return False


class Edge(object):

	__table_decl__ = "CREATE TABLE edge ( head_id INTEGER, tail_id INTEGER," \
			 "PRIMARY KEY (head_id, tail_id)," \
			 "FOREIGN KEY (head_id) REFERENCES node(id)," \
			 "FOREIGN KEY (tail_id) REFERENCES node(id) )"

	__storm_table__ = "edge"
	__storm_primary__ = "head_id", "tail_id"
	head_id = Int()
	tail_id = Int()
	head = Reference(head_id, Node.id)
	tail = Reference(tail_id, Node.id)

	def __init__(self, head, tail):
		self.head_id = head
		self.tail_id = tail


	def __repr__(self):
		return "{0} -> {1}".format( self.head_id, self.tail_id )


class Graph(object):

	@staticmethod
	def __create_tables__(graph):
		import sqlite3
		try:
			graph.storm.execute( Node.__table_decl__, noresult=True )
		except( sqlite3.OperationalError ):
			pass
		try:
			graph.storm.execute( Edge.__table_decl__, noresult=True )
		except( sqlite3.OperationalError ):
			pass


	def __init__(self, db_url):
		# we have to tell storm that we want sqlite
		storm_db = create_database('sqlite:%s' % db_url)
		self.storm = Store(storm_db)


	def create_node(self, content):
		n = Node( content )
		self.storm.add(n)
		return n


	def remove_nodes(self, *nodes):
		for n in nodes:
			self.storm.remove(n)


	def node(self, id):
		return self.storm.get(Node, id)


	def nodes(self, *args, **kvargs):
		if len(args) == 0 and len(kvargs) == 0:
			return self.storm.find(Node)
		else:
			return self.storm.find(Node, *args, **kvargs)


	def commit(self):
		self.storm.commit()

