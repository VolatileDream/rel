# rel

Command line program to store directed graph relationships between bits of content

---

rel is a simple program that handles relatedness of pieces of content.

rel is backed by a minimal wrapper around [Storm](https://storm.canonical.com/)
to support a Directed Graph (rel/graph.py) in [sqlite3](https://sqlite.org/)
storage. It uses [PlyPlus](https://github.com/erezsh/plyplus) to support a
lisp-like query language (rel/lisp.py) when listing or searching for nodes
(see rel/query.py for all functions, look for @expose or @expose_as).

## Command Line Invocation

See `rel --help`

