#!/usr/bin/python2

import sys
import base64
import re
import json
import requests
import urllib
import ConfigParser
import StringIO

def webrequest(url):
	try:
		res = requests.get(url)
	except Exception as e:
		print('URL: %s\nException: %s' % (url, str(e)))
	if res == 0:
		print('ERROR: res == 0')
		return dict()
	res.raise_for_status()
	return res.json()

def getissues(urlprefix, depissue):
	out = dict()
	params = {
		'bug_status'	: ['NEW','ASSIGNED','REOPENED','VERIFIED','NEEDINFO'],
		'blocks'		: [depissue],
		'order'			: 'bugs.creation_ts desc',
	}
	url = '%s/bug?%s' % (urlprefix, urllib.urlencode(params, True))
	res = webrequest(url)
	if 'bugs' not in res:
		return out
	bugs = res['bugs']
	showurl = urlprefix.replace('rest', 'show_bug') + '?id={0}'
	for bug in bugs:
		id = '%d' % bug['id']
		url = '%s/bug/%s/attachment' % (urlprefix, id)
		res = webrequest(url)
		if 'bugs' not in res or id not in res['bugs']:
			continue
		idef = ''
		for att in res['bugs'][id]:
			if not att['is_obsolete'] and att['file_name'] == 'issue.def':
				idef = base64.b64decode(att['data'])
				break
		if idef:
			out[id] = {
				'def': idef,
				'url': showurl.format(id),
				'desc': bug['summary']
			}
	return out

def bugzilla_check(buglist, desc, testruns, issues):
	out = []
	for id in buglist:
		# check each bug to see if it is applicable and exists
		applicable = True
		# parse the config file which describes the issue
		config = ConfigParser.ConfigParser()
		config.readfp(StringIO.StringIO(buglist[id]['def']))
		sections = config.sections()
		req = idesc = ''
		for key in sections:
			if key.lower() == 'requirements':
				req = key
			elif key.lower() == 'description':
				idesc = key
		# verify that this system & multitest meets the requirements
		if req:
			for key in config.options(req):
				val = config.get(req, key)
				if key.lower() == 'mode':
					applicable = (desc['mode'] in val)
				else:
					applicable = (val.lower() in desc['sysinfo'].lower())
		if not applicable or not idesc:
			continue
		# check for the existence of the issue in the data
		bugdata = {
			'id': id,
			'desc': buglist[id]['desc'],
			'bugurl': buglist[id]['url'],
			'found': '',
		}
		for key in config.options(idesc):
			if bugdata['found']:
				break
			val = config.get(idesc, key)
			if key.lower().startswith('dmesgregex'):
				for issue in issues:
					if re.match(val, issue['line']):
						urls, host = issue['urls'], desc['host']
						url = urls[host] if host in urls else ''
						bugdata['found'] = url
						break
		out.append(bugdata)
	return out

def pm_stress_test_issues():
	return getissues('http://bugzilla.kernel.org/rest.cgi', '178231')

if __name__ == '__main__':

	bugs = pm_stress_test_issues()
	for id in bugs:
		print('ISSUE ID   = %s' % id)
		print('ISSUE DESC = %s' % bugs[id]['desc'])
		print('ISSUE URL  = %s' % bugs[id]['url'])
		print('ISSUE DEFINITION:')
		print(bugs[id]['def'])
