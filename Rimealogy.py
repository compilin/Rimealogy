#!/usr/bin/env python3
import xml.etree.ElementTree as ET
from sys import argv

def nodeToString(node):
	if len(node.attributes) > 0:
		return "%s[%s]" % (node.tag, ",".join('%s="%s"' % a for a in node.attributes.items()))
	else:
		return node.tag

def printPath(node):
	return ">".join( nodeToString(n) for n in pathTo(node) )

def pathFrom(node, path):
	if node is None:
		return None
	if type(path) == str:
		try:
			return [n for n in node if n.tag == path][0]
		except IndexError:
			return None
	else:
		if len(path) == 0:
			return node
		else:
			return pathFrom(pathFrom(node, path[0]), path[1:])

class Faction:
	def __init__(self, game, node):
		try:
			self.game = game
			self.name = node.findtext('name')
			self.factionId = int(node.findtext('loadID') or 0)
			self.factionDef = node.findtext('def')
			self.leader = node.findtext('leader')
			if self.leader != 'null':
				self.leader = self.leader[6:] # Remove the Thing_ prefix
			self.relations = {
				x.findtext('other'): int(float(x.findtext('goodwill') or '0')) for x in node.find('relations') if x.tag == 'li'
			}
		except:
			if 'factionId' in dir(self):
				print("Error occured while processing node %s" % self.factionId)
			raise
	
	def __str__(self):
		return "Faction %d '%s'" % (self.factionId, name)
	
	def __repr__(self):
		return '<Faction id=%d def="%s" name="%s">' % (self.factionId, self.factionDef, self.name)
		
from collections import namedtuple

class Relation(namedtuple('Relation', ['type', 'other'])):
	def __new__(cls, node):
		return super(Relation, cls).__new__(cls, node.findtext('def'), node.findtext('otherPawn')[6:])

class Name:
	def __init__(self, node):
		if node.tag != 'name':
			raise RuntimeError("Given node is not a name node")
		self.isNull = node.get('IsNull') == "True"
		if not self.isNull:
			self.nameType = node.get('Class')
			if self.nameType == "NameTriple":
				self.first = node.findtext('first')
				self.nick = node.findtext('nick')
				self.last = node.findtext('last')
			elif self.nameType == "NameSingle":
				self.first = self.last = ""
				self.nick = node.findtext('name')
		else:
			self.first = self.nick = self.last = "???"
			self.nameType = "Null"
	
	def getFullName(self):
		if self.isNull:
			return "???"
		elif self.nameType == "NameTriple":
			if self.nick == self.first:
				return "'%s' %s" % (self.first, self.last)
			elif self.nick == self.last:
				return "%s '%s'" % (self.first, self.last)
			else:
				return "%s '%s' %s" % (self.first, self.nick, self.last)
		elif self.nameType == "NameSingle":
			return "'%s'" % self.nick
	
	def __str__(self):
		return self.getFullName()
	
	def __repr__(self):
		return "<Name type='%s' first='%s' nick='%s' last='%s'>" % (self.nameType, self.first, self.nick, self.last)
		

class Pawn:
	def __init__(self, game, node):
		try:
			self.game = game
			self.alive = node.findtext('./healthTracker/healthState') != 'Dead'
			self.pawnId = node.findtext('id')
			self.name = Name(node.find('name'))
			self.pawnDef = node.findtext('def')
			self.gender = node.findtext('gender') or 'Male'
			self.faction = node.findtext('faction') if len(node.findall('faction')) > 0 else "None"
			self.kindDef = node.findtext('kindDef')
			
			social = node.find('social')
			self.seen = social.findtext('everSeenByPlayer') != "False"
			self.relations = []
			self.parents = set()
			self.children = set()
			for li in social.find('directRelations'):
				if 'Human' in li.findtext('otherPawn'):
					rel = Relation(li)
					if rel.type == 'Parent':
						self.parents |= set([rel.other])
					else:
						self.relations.append(rel)
		except:
			if 'pawnId' in dir(self):
				print("Error occured while processing node %s" % self.pawnId)
			raise
		
	def __str__(self):
		return "%s %s" % (self.pawnDef, name)
	
	def __repr__(self):
		return '<Pawn def="%s" id="%s" faction="%s" name="%s" gender="%s" kind="%s">' % (self.pawnDef, self.pawnId, self.faction, self.name.getFullName(), self.gender, self.kindDef)

class Game:
	def __init__(self, node):
		self.factions = {
				("Faction_%d" % f.factionId): f for f in [Faction(self, x) for x in node.find('./world/factionManager/allFactions')]
			}
		self.humans = { p.pawnId: p for p in [Pawn(self, x) for x in node.findall('.//*[def="Human"]')] }
		self.playerFaction = [i for i,f in self.factions.items() if f.factionDef == "PlayerColony"][0]
		
		for k,v in self.humans.items():
			for child in v.parents:
				offspring = self.humans[child]
				offspring.children |= set([k])
	

def getCoupleId(cop):
	return "Couple_" + "_".join(cop)


if __name__ == "__main__":
	if len(argv) < 2:
		print("Must supply input filename")
		exit(1)
	
	drawall = False if len(argv) < 4 else True
	
	filename = argv[1]
	print("Parsing file %s" % filename)
	doc = ET.parse(filename)
	print("Retreiving game data")
	game = Game(doc.find('game'))
	
	display = set([None])
	if not drawall:
		nextPawns = set([k for k,h in game.humans.items() if h.faction == game.playerFaction ])
	else:
		nextPawns = set([k for k,h in game.humans.items() if h.seen ])
	newPawns = set()

	while len(nextPawns) > 0:
		display |= nextPawns
		for nxt in nextPawns:
			pawn = game.humans[nxt]
			if pawn.seen:
				newPawns |= set(filter(lambda x: x in game.humans, pawn.parents | set(pawn.children)))
		newPawns -= display
		newPawns -= nextPawns
		nextPawns = newPawns
		newPawns = set()

	seen = set(k for k,v in game.humans.items() if v.seen) | \
			set(r.other for col in game.humans.values() if col.faction == game.playerFaction for r in col.relations)
	display |= set(r.other for col in game.humans.values() if col.faction == game.playerFaction for r in col.relations)
	
	print("Filtering pawns to show ... %d selected" % len(display))
	
	factionCols = dict()
	for k,fac in game.factions.items():
		if k == game.playerFaction:
			factionCols[k] = "#DDDDFF"
		else:
			if game.playerFaction not in fac.relations or fac.relations[game.playerFaction] == 0:
				factionCols[k] = "#DDDDDD"
			elif fac.relations[game.playerFaction] > 0:
				factionCols[k] = "#DDFFDD"
			elif fac.relations[game.playerFaction] < 0:
				factionCols[k] = "#FFDDDD"
	virtualNodeId = 0
	
	outfilename = "./tree.dot" if len(argv) < 3 else argv[2]
	print("Writing to file %s" % outfilename)
	with open(outfilename, 'w') as file:
		file.write('digraph Geneaolgy {\n')
		file.write('\tgraph [overlap=prism,rankdir=LR,splines=line,outputorder=edgesfirst];\n' +
					'\tnode [label="",shape=box,style=filled];\n')

		for n,h in sorted(game.humans.items()):
			if n in display:
				if n in seen:
					label = h.name.getFullName()
					fillcol = factionCols[h.faction]
					if not h.alive:
						label += "💀"
				else:
					label = "???"
					fillcol = "#EEEEEE"
				file.write('\t%s [label="%s",fillcolor="%s"];\n' % (n, label, fillcol))
			if h.faction == game.playerFaction:
				for r in sorted(h.relations, key=lambda x: x.other):
					style = "dotted"
					if 'Spouse' in r.type:
						style = "bold"
					elif 'Fiance' in r.type:
						style = "dashed"
					color = "black"
					if 'Ex' in r.type:
						color = "brown"
					elif not (h.alive and game.humans[r.other].alive):
						color = "#80800080"

					if game.humans[r.other].faction != game.playerFaction or n < r.other:
						tt = "%s <%s> %s" % (h.name.nick, r.type, game.humans[r.other].name.nick)
						file.write('\t%s -> %s [xlabel="%s",constraint=false,dir=both,style=%s,color="%s",tooltip="%s",labeltooltip="%s"];' % 
							(n, r.other, r.type, style, color, tt, tt))
					virtNode = 'Virtual_%s' % virtualNodeId
					file.write('\t%s [style=invis];\n' % virtNode)
					file.write('\t%s -> %s [style=invis];\n' % (virtNode, n))
					file.write('\t%s -> %s [style=invis];\n' % (virtNode, r.other))
					virtualNodeId += 1

		couples = set()

		for cop in set([ frozenset(h.parents) for k,h in game.humans.items() if k in display]):
			if any((c in display) for c in cop):
				couples |= set([getCoupleId(cop)])
				file.write('\t%s [label="",shape=point];\n' % getCoupleId(cop))
				for c in cop:
					if c in display:
						file.write('\t%s -> %s [arrowhead=none];\n' % (c, getCoupleId(cop)))

		for n,h in sorted(game.humans.items()):
			if n in display:
				if len(h.parents) > 0 and getCoupleId(h.parents) in couples:
					file.write('\t%s -> %s;\n' % (getCoupleId(h.parents), n))

		file.write('}')
	
	print("Finished. Recommended parameters for graphviz:\ndot -Tsvg tree.dot > tree.svg")    
	
	
