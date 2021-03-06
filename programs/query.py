#!/usr/bin/env python

###############################################################################
# query.py - A command line program for creating, retrieving, updating, and   #
#	     deleting data from the GlueX Metadata Database.		      # 
# Written by Joshua Freedman						      #
###############################################################################

import os
import sys
import argparse
from gluex_metadb_utils import databaseconnection as DBC
from gluex_metadb_utils import constants as consts
from gluex_metadb_utils import metadatamodel

# all the tables in one string, for epilog
table_str = ''
for table in DBC.DatabaseConnection.get_tables():
	table_str += '  {}\n'.format(table)

# argparse setup
parser = argparse.ArgumentParser(description='Manipulates/retrieves data from the GlueX Metadata Database',
	formatter_class=argparse.RawDescriptionHelpFormatter,
	epilog='The tables in the database are:\n' + table_str)
parser.add_argument('table',help='the table that will be manipulated/retrieved from')
parser.add_argument('-a','--add',nargs='+',metavar='attributeName attributeValue',
	help='adds an entry to the specified table with the specified attributes, arguments should be in name value pairs')
parser.add_argument('-e','--edit',nargs=3,metavar=('index','attribute','newValue'),
	help='changes the specified index\'s value for the specified attribute')
parser.add_argument('-d','--delete',type=int,metavar='index',
	help='deletes the specified index from the specified table')
parser.add_argument('-s','--search',nargs=2,metavar=('attribute','searchKey'),
	help='searches a table for any entries that have the specific attribute value combination and lists them.')
parser.add_argument('-l','--list',action='store_true',
	help='lists the contents of the entire table')
parser.add_argument('--show-attributes',action='store_true',
	help='shows the manipulatable attributes of the specified table')
parser.add_argument('-v','--verbose',action='store_true',
	help='prints success messages when operations are successful')
args = parser.parse_args()

# DatabaseConnection object setup
try:
	db = DBC.DatabaseConnection(os.environ[consts.DB_ENV_VAR])
except DBC.InvalidDatabaseURLException as exc:
	print exc
	sys.exit(1)
except KeyError:
	print 'Set the environment variable \"{}\" to a valid database URL.'.format(consts.DB_ENV_VAR)
	sys.exit(1)

# checks if the table is a valid table
try:
	DBC.DatabaseConnection.check_table(args.table)
except DBC.TableError as exc:
	print exc
	sys.exit(1)

# run the add procedures
if args.add is not None: 
	if len(args.add) % 2 == 0:
		for arg in args.add:
			try:
				args.add[args.add.index(arg)] = int(arg)
			except ValueError:
				pass	
		dictToAdd = dict(zip(args.add[::2],args.add[1::2]))
		try:
			db.create(args.table,dictToAdd)
			if args.verbose:
				print 'Successfully added an entry into \"{}\" table.'.format(args.table)
		except (AttributeError,IOError) as exc:
			print exc
	else:
		print 'Arguments must be supplied in pairs as followed: attribute1 value1 attribute2 value2... and so on.'

# run the delete procedures
if args.delete is not None:
	try:
		db.remove(args.table,args.delete)
	except IndexError as exc:
		print exc
	else:
		if args.verbose:
			print 'Successfully deleted index \"{}\" from table \"{}\".'.format(args.delete,args.table)

# run the edit procedures
if args.edit is not None:
	args.edit[0] = int(args.edit[0])
	try:
		args.edit[2] = int(args.edit[2])
	except ValueError:
		pass	

	try:
		db.update(args.table,args.edit[0],args.edit[1],args.edit[2])
	except (IndexError, AttributeError) as exc:
		print exc
	else:
		if args.verbose:
			print 'Successfully updated index \"{}\" from table \"{}\".'.format(args.edit[0],args.table)

# run the search procedures
if args.search is not None:
	try:
		args.search[1] = int(args.search[1])
	except ValueError:
		pass

	try:
		results = db.search(args.table,args.search[0],args.search[1])
		if not results:
			print 'No entries exist in table \"{}\" that match the search criteria.'.format(args.table)
		else:
			for entry in results:
				print repr(entry)
	except AttributeError as exc:
		print exc

# run the show attributes procedures
if args.show_attributes:
	print 'Attributes for "{}":'.format(args.table)
	message = False
	for attr in db.get_attributes(args.table):
		try:
			getattr(getattr(metadatamodel,args.table),attr + 'Id')
		except AttributeError:
			extra = ''
		else:
			extra = '*'
			message = True
		print extra + attr
	if message is True:
		print '\n*when manipulating these values, use the record\'s "id" value and add "Id" to the end of attribute name'
		print 'ex: DataTypeId 1 or SoftwareVersionId 10'

# run the list table procedures
#if args.show_tables:
#	print ''
#	for table in db.get_tables():
#		print table

# run the list procedures
if args.list:
	if not db.list_all(args.table):
		print args.table + ' table is empty.'
	else:
		for entry in db.list_all(args.table):
			print repr(entry)	
