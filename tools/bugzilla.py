#!/usr/bin/python2

import sys
import base64
import json
import requests
import urllib

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
