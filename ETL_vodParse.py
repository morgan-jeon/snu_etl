class vodParse:
	from selenium import webdriver
	from selenium.webdriver.firefox.service import Service
	from webdriver_manager.firefox import GeckoDriverManager
	import time

	driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()))

	driver.get('http://etl.snu.ac.kr/')

	driver.find_element_by_id('input-username').send_keys('morgan.jeon')
	driver.find_element_by_id('input-password').send_keys('')
	driver.find_element_by_name('loginbutton').click()
	# login = input("[*] 로그인 후 엔터를 누르세요.")
	time.sleep(2)
	courses = driver.find_elements_by_class_name('course_link')
	course = []
	vod = []
	for url in courses:
		course.append(url.get_attribute('href'))
	for url in course:
		driver.get(url)
		activitys = driver.find_elements_by_css_selector("a[class='']")
		for activity in activitys:
			href = activity.get_attribute('href')
			if 'vod' in href:
				name = activity.find_element_by_class_name('instancename').text.split('\n')[0]
				vod.append({'name':name, 'url':href})

	result = []
	for video in vod:
		video_url = video['url'].replace('view','viewer')
		driver.get(video_url)
		try:
			obj = driver.switch_to.alert
			obj.accept()
		except:
			print("no alert")

		test = driver.execute_script("var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {}; var network = performance.getEntries() || {}; return network;")
		for item in test:
			if 'playlist.m3u8' in item['name']:
				plisturl = item['name']
				print(plisturl)
		if 'm3u8' in plisturl:
			result.append({'name':video['name'],'url':plisturl})

	with open('vodlist.txt', 'wt', encoding="utf-8") as f:
		for a in result:
			f.write(a['name']+"|"+a['url']+'\n')

class vodDownload:
	import requests, tqdm
	import asyncio, os
	import aiohttp, aiofiles, aiodns
	import json

	def download(m3u8url, fname):
		playlist = requests.get(m3u8url).text.split('\n')
		playlist_uri = []
		for line in playlist:
			if '#' not in line:
				if line != '':
					playlist_uri.append(line)

		m3u8uri = m3u8url.split('/')
		del(m3u8uri[-1])

		urlhost = '/'.join(m3u8uri)
		playlist_url = urlhost+'/'+playlist_uri[0]
		vod_m3u8 = requests.get(playlist_url).text.split('\n')
		ts_url = []
		for line in vod_m3u8:
			if '#' not in line:
				if line != '':
					ts_url.append(urlhost+'/'+line)

		count = len(ts_url)
		print(fname)
		pbar = tqdm.tqdm(total=count)
		for x in range(0, count):
			name = ts_url[x].split('/')[-1]
			asyncio.run(downURL(ts_url[x], name, pbar))
		pbar.close()

		with open(fname+".mp4", 'wb') as vod:
			for i in range(0, count):
				name = ts_url[i].split('/')[-1]
				with open(os.path.join('tmp', name), 'rb') as tmp:
					vod.write(tmp.read())

	async def downURL(url, name, pbar):
		try:
			with requests.get(url) as resp:
				with open(os.path.join('tmp', name), 'wb') as f:
					f.write(resp.content)
		except Exception as e:
			print(e)
		pbar.update(1)

	def main():
		with open('vodlog.txt', 'rt', encoding="utf-8") as st_json:
		    log = json.load(st_json)

		logdict = log
		with open('vodlist.txt', 'rt', encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:
				l = line.replace('\n','').split('|')
				if l[0] not in log:
					print(f'[*] Downloading {l[0]}')
					logdict.append(l[0])
					download(l[1], l[0])
				else:
					print(f'[*] Already downloaded {l[0]}')

		print(logdict)
		with open('vodlog.txt', 'wt', encoding="utf-8") as logwrite:
			logwrite.write(json.dumps(logdict, ensure_ascii=False))	

	if __name__=="__main__":
		main()