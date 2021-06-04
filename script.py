#!python3

import os
import sys
import json
import requests
import zipfile
import shutil

def zipdir(path, zipname):
    ziph = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), 
                       os.path.relpath(os.path.join(root, file), 
                                       os.path.join(path, '..')))
    ziph.close()

CLOUDFLARE = 1
NETLIFY    = 2

SERVICE = NETLIFY

APEX_DOMAIN = "optym.tech"

API_KEY = os.environ['NETLIFY_PERSONAL_ACCESS_TOKEN']

def print_green(m):
	print('\033[92m' + m + '\033[0m')

def deploy(subdomain, config):
	os.system("mkdir temp")
	os.chdir("temp")
	
	print_green("Cloning repository")
	os.system("git clone " + config['repository'] + " repo")
	os.chdir("repo")
	
	print_green("Setting Config")
	siteConfig = json.dumps(config['siteConfig'])
	f = open('src/config.js', 'w')
	f.write('export default ' + siteConfig)
	f.close()

	print_green("Building")
	for command in config['commands']:
		os.system(command)
	
	print_green("Zipping")
	zipdir(config['directory'], "build.zip")
	
	print_green("Deploying")
	f = open("build.zip", "rb")
	zip_contents = f.read()
	f.close()
	
	url = subdomain + '.' + APEX_DOMAIN

	r = requests.post("https://api.netlify.com/api/v1/sites", headers={'Authorization': "Bearer " + API_KEY, 'Content-Type': "application/json"}, json={'custom_domain': url})
	print(r.text)
	r = requests.put("https://api.netlify.com/api/v1/sites/" + url, headers={'Authorization': "Bearer " + API_KEY, 'Content-Type': "application/zip"}, data=zip_contents)
	print(r.text)
	r = requests.post("https://api.netlify.com/api/v1/sites/" + url + "/ssl", headers={'Authorization': "Bearer " + API_KEY})
	print(r.text)
	
	print_green("Cleaning up")
	os.chdir('../..')
	shutil.rmtree("temp")

def main():
	if len(sys.argv) == 1:
		print("1 argument expected")
		return
	
	filename = sys.argv[1]

	if not filename.startswith("subdomains/"):
		return

	if not filename.endswith(".json"):
		return

	file = open(filename)
	contents = file.read()
	config = json.loads(contents)
	file.close()

	subdomain = os.path.basename(filename)[:-5]

	deploy(subdomain, config)
	return

if __name__ == '__main__':
	main()
