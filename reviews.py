import codecs, json, os, codecs, logging
from pprint import pprint
from collections import namedtuple
from git import Repo
from git.remote import RemoteProgress
from requests import get
import whatthepatch
from sh import git, ls, cd, cat

Blame = namedtuple('Blame', ['lines','commit'])

class Marvin(object):
	"""Merely A ReView INcentivizer """
	def __init__(self, repo_storage_path=None):
		class ProgressHandler(RemoteProgress):
			def line_dropped(self, line):
				logging.info(line)
			def update(self, *args):
				logging.info(self._cur_line)
		logging.info('Marvin started!')
		self.progress = ProgressHandler()
		if repo_storage_path is None:
			repo_storage_path = 'repos'
		self.repo_storage_path = os.path.abspath(repo_storage_path)

	def handle_pr(pull_request):
		repo_info = self._parse_github_pull_request(pull_request)
		logging.info('Repo info: %s' % repo_info)
		logging.info('Storing repos to: %s' % self.repo_storage_path)
		self.repo = self._get_repo(**repo_info)
		self.diff = self.analyze_diff(diff_url=pull_request['diff_url'])

	def _parse_github_pull_request(self, pull_request):
		logging.info('Parsing PR #%s:%s' % (pull_request['number'], pull_request['title']))
		logging.info('HTML url: %s' % pull_request['html_url'])
		clone_url = pull_request['head']['repo']['clone_url']
		full_name = pull_request['head']['repo']['full_name']
		branch = pull_request['head']['ref']
		return {'full_name': full_name, 
				'clone_url': clone_url,
				'branch': branch}

	def _get_repo(self, full_name, clone_url=None, branch=None):
		repo_path = os.path.join(self.repo_storage_path, full_name)
		if os.path.isdir(os.path.join(repo_path, '.git')):
			logging.info(full_name, '%s was already cloned.')
			return Repo(repo_path)
		else:
			return self._clone_repo(clone_url, repo_path, branch)

	def _clone_repo(self, clone_url, clone_path, branch):
		# depth = 1
		logging.info('Cloning into %s' % clone_path)
		return Repo.clone_from(clone_url, clone_path,
			progress=self.progress,
			branch=branch)
			# depth=depth)

	def analyze_diff(self, diff_url=None, diff_path=None):
		diff = self._get_diff(diff_url, diff_path)
		return self._process_diff(diff)

	def _get_diff(self, diff_url=None, diff_path=None):
		if diff_url is not None:
			logging.info('Fetching diff from: %s' % diff_url)
			diff = get(diff_url).text
		elif diff_path is not None:
			logging.info('Reading local diff from: %s' % diff_path)
			with open(diff_path) as f:
				diff = f.read()
		else:
			raise Exception('Have to provide either diff_url or diff_path parameter!')
		return diff

	def _process_diff(self, diff):
		def status(change):
			if change[0] is None:
				return 'insert'
			elif change[1] is None:
				return 'delete'
			else:
				return 'equal'
		out = []
		for hunk in whatthepatch.parse_patch(diff):
			file_changes = []
			in_changeset = False
			for mode in [('insert',1), ('delete',0)]:
				for change in hunk.changes:
					if status(change) == mode[0] and not in_changeset:
						in_changeset = True
						file_changes.append({'start':change[mode[1]], 'type':mode[0]})
					elif status(change) == 'equal' and in_changeset:
						in_changeset = False
						file_changes[-1]['end'] = change[mode[1]]-1
			out.append({'header':hunk.header, 'changes':file_changes})
		return out

	def blame_surrounding_lines(self, changeset):
		file_path = changeset['header'].new_path
		logging.info('git blaming %s' % file_path)
		changes = changeset['changes']
		inserts = [x for x in changes if x['type'] == 'insert']
		cd('repos/hpi-swt2/wimi-portal')
		out = {}
		for insert in inserts:
			for line in [insert['start'] - 1, insert['end'] + 1]:
				blame_out = git('--no-pager', 'blame', file_path, '-L' + str(line) + ',+1', '-l')
				commit_hash = blame_out.split(' ')[0]
				if commit_hash in out:
					out[commit_hash].append(line)
				else:
					out[commit_hash] = [line]
		return out


if __name__ == "__main__":
	# print('Using an example pull request')
	# path = '338.json'
	# print('Loading pr from:', path)
	# with codecs.open(path, 'r', encoding='utf-8') as f:
	# 	pr = json.loads(f.read())
	# bot = Marvin(pr, repo_storage_path='repos')

	# print('*'*20)
	# print(bot.repo.working_dir)
	# print(bot.repo.description)
	# print(bot.repo.active_branch)
	# print('*'*20)
	# pprint(bot.get_changes())

	# rev = 'd34b7de78259a2e83ec7cfc16bff084ad1d4685c'
	# file = 'app/assets/stylesheets/application.css'
	# blame_infos = bot.repo.blame(rev, file)
	# [
	#  [<git.Commit "c78b9c1c0a57cc62505a377726f000b00c2e8f66">,
	#	['    background-color: #FFFFFF;']],
	#  [<git.Commit "b57effdfe706d5b24b53cc780395ea9bfc5fcab8">,
	#	['    padding: 15px;']]
	# ]

	# pprint(blame_infos)

	logging.basicConfig(level=logging.INFO)

	marvin = Marvin()
	file_changes = marvin.analyze_diff(diff_path='338.diff')

	# pprint(changes)
	single_file_changes = [x for x in file_changes if x['header'].new_path == 'app/controllers/work_days_controller.rb'][0]
	blame = marvin.blame_surrounding_lines(single_file_changes)

	pprint(blame)
	# inserts = [x for x in single_file_changes if x['changes']['type'] == 'insert']
	# authors = marvin.get_surrounding_authors()

	# pprint(changes)

	# pprint(changeset)