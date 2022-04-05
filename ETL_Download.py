import sqlite3
import requests, tqdm
import asyncio, os
import aiohttp, aiofiles, aiodns

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

	with open(os.path.join("vod",name+".mp4"), 'wb') as vod:
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
	con = sqlite3.connect("./etl.db")
	cursor = con.cursor()
	query = f"SELECT name, playlist, id FROM vod WHERE download = 0"
	cursor.execute(query)
	rows = cursor.fetchall()
	for row in rows:
		print(f'[*] Downloading {row[0]}')
		download(row[1], row[0])
		cursor.execute(f"UPDATE vod SET download = 1 WHERE id == {row[2]}")
		con.commit()
	con.close()

if __name__=="__main__":
	main()
