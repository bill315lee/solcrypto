#!/usr/bin/env python
from __future__ import print_function
"""
This merkle tree implementation uses a balanced binary tree, for example a 
tree containing 5 leafs has 3 nodes and 1 root.

        r
       / \ 
      n3  L5
      /\
     /  \
    /    \
   n1     n2
  / \    / \
 L1  L2 L3 L4

When hashing the leafs and nodes the highest bit is reserved for the proof
to store the left or right attribute. Example proof of L1:

  H(H(H(L1, L2), n2), L5) = r

The proof supplied for L1 is:

   L2, n2, L5

To prove L2 instead of L1 the proof supplied is:

   L1, n2, L5

The highest bit of each item in the proof determines if it's the 
left or right argument to the hash function.

Whereas to prove L5 the proof would be:

	n3

To verify the proof:

	r = H(n3, L5)

As you can see the `n3` entry takes the lhs param in order to preserve
the ordering property of the hash function by sacrificing a bit.

The 'balanced' terminology here may be different from the common understanding
of balanced, here it means that every node always has 2 children. 

Interesting references:

 - https://en.wikipedia.org/wiki/K-ary_tree
 - http://www.jaist.ac.jp/~mizuhito/papers/conference/CADE05.pdf
 - http://ijns.jalaxy.com.tw/contents/ijns-v3-n1/ijns-2006-v3-n1-p65-72.pdf
 - https://kylelemons.net/download/Complex_Data_Structures_N-ary_Tree_PDF.pdf
"""

import random

from .utils import hashs, bit_clear, bit_set, bit_test, tobe256

merkle_hash = lambda *x: bit_clear(hashs(*x), 256)


def merkle_tree(items):
	# Given an array of items, build a merkle tree
	assert len(items) > 0
	level = map(merkle_hash, items)

	# Single item in a tree is its own root...
	if len(items) == 1:
		return [level], level[0]

	tree = []
	keep = []
	while True:
		# When node has been pushed up, append to current level
		if len(keep):
			level += keep
			keep = []

		# Unbalanced level - push last node up to the level above
		if len(level) % 2 == 1:
			keep.append(level[-1])
			level = level[:-1]

		tree.append(level)
		it = iter(level)
		level = [merkle_hash(item, next(it)) for item in it]
		
		# Tree has finally been reduced down to a single node
		if len(level) == 1 and not len(keep):
			tree.append(level)
			break
	return tree, tree[-1][0]


def merkle_path(item, tree):
	"""
	Create a merkle path for the item within the tree
	max length = (height*2) - 1
	min length = 1
	"""
	item = merkle_hash(item)
	path = []
	for level in tree:
		if item not in level:
			continue
		if len(level) == 1:
			assert tree[-1][0] == item
			return path
		idx = level.index(item)
		if 0 == idx % 2:
			path.append(bit_set(level[idx+1], 256))
			item = merkle_hash(item, level[idx+1])
		else:
			path.append(level[idx-1])
			item = merkle_hash(level[idx-1], item)


def merkle_proof(leaf, path, root):
	"""
	Verify merkle path for an item matches the root
	"""
	node = merkle_hash(leaf)
	for item in path:
		if bit_test(item, 256):
			item = bit_clear(item, 256)
			node = merkle_hash(node, item)
		else:
			node = merkle_hash(item, node)
	return node == root


if __name__ == "__main__":
	
	for i in range(1, 100):
		items = range(0, i)
		tree, root = merkle_tree(items)
		random.shuffle(items)
		for item in items:
			proof = merkle_path(item, tree)
			assert True == merkle_proof(item, proof, root)
	
	# Test items, 0..9
	items = [hashs(n) for n in range(0, 10)]
	tree, root = merkle_tree(items)
	item = items[3]
	proof = merkle_path(item, tree)
	merkle_proof(item, proof, root)

	# Expected output test case
	assert root == 0x1a792cf089bfa56eae57ffe87e9b22f9c9bfe52c1ac300ea1f43f4ab53b4b794
	assert merkle_hash(item) == 0x2584db4a68aa8b172f70bc04e2e74541617c003374de6eb4b295e823e5beab01
	assert proof[0] == 0x1ab0c6948a275349ae45a06aad66a8bd65ac18074615d53676c09b67809099e0
	assert proof[3] == 0xcb431dd627bc8dcfd858eae9304dc71a8d3f34a8de783c093188bb598eeafd04

	print("")
	print(','.join([
		'"0x' + tobe256(root).encode('hex') + '"',
		'"0x' + tobe256(merkle_hash(item)).encode('hex') + '"',
		'[' + ','.join(['"0x' + tobe256(x).encode("hex") + '"' for x in proof]) + ']'
	]))
