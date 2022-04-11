import requests
import bs4
import sqlite3

def etl_login(s):
	s.get("http://etl.snu.ac.kr/")
	s.get("http://etl.snu.ac.kr/index.php")
	s.get("http://etl.snu.ac.kr/login.php")
	
	password = input("Password? ")

	login_payload = {
		"si_id": "morgan.jeon", 
		"si_pwd": "Moso1206!!", 
		"si_redirect_address": "https://sso.snu.ac.kr/snu/ssologin_proc.jsp?si_redirect_address=http://etl.snu.ac.kr/"
	}
	req_sso = s.post("https://sso.snu.ac.kr/safeidentity/modules/auth_idpwd", data=login_payload)
	
	login_cred = {}
	bs = bs4.BeautifulSoup
	login_soup = bs(req_sso.text, "lxml")
	for form in login_soup.find_all("input"):
		name = form['name']
		value = form['value']
		login_cred[name] = value
	req_etl = s.post("https://sso.snu.ac.kr/nls3/fcs", data=login_cred)
	return req_etl

def etl_parse(s):
	etl_req = s.get('http://etl.snu.ac.kr/').content
	bs = bs4.BeautifulSoup
	etl_soup = bs(etl_req, "lxml")
	course_link = etl_soup.find_all("a", class_="course_link")
	courses = []
	for a in course_link:
		child = a.find("div", class_="course-title")
		title = child.find("h3").contents[0]
		prof = child.find("p", class_="prof").contents[0]
		link = a["href"]
		id = link.split("?")[-1].split("=")[1]
		courses.append({"title":title, "prof":prof, "url":link, "id": id})
	return courses

def activity_parse(s, url, course_title):
	req_course = s.get(url)
	bs = bs4.BeautifulSoup
	course_soup = bs(req_course.text, 'lxml')
	course_soup_all = course_soup.find("div", class_="total_sections")
	week_soup = course_soup_all.find("ul", class_="weeks")
	weeks_soup = week_soup.find_all("li", class_="section")
	for week in weeks_soup:
		week_name = week.find('div', class_='content').find('h3', class_='sectionname').contents[0]
		week_name = week_name.split('주차')[0].split('Week')[0]
		img_text = week.find('div', class_='content').find('ul', class_='img-text')
		data = {}
		if img_text != None:
			print(f"[ {week_name}주차 ]")
			for acti in img_text.find_all('li', class_='activity'):
				act_name = acti.find("span", class_="instancename").contents[0]
				if acti.find("a") == None:
					print("Not Allowed Activity")
				else:
					act_url = acti.find("a")['href']
					act_type = acti['class'][1]
					if act_type not in ['quiz', 'feedback', 'url', 'zoom', 'choice', 'ubboard']:
						tmp = acti.find("span", class_="displayoptions")
						if tmp.find("span") == None:
							act_desc = tmp.contents[0]
						else:
							act_desc = tmp.find("span").contents[0]
					else:
						act_desc = ""
					
					act_id = act_url.split("=")[-1]

					if "~" in act_desc:
						parse_date(act_desc)
						dbsave("activity", {"id":act_id,"name":act_name,"subject":course_title,"type":act_type,"url":act_url,"date":1}, act_id)
						dbsave("due", {"id":act_id,"start":act_desc.split(" ~ ")[0],"end":act_desc.split(" ~ ")[1],"did":0}, act_id)
					else:
						dbsave("activity", {"id":act_id,"subject":course_title,"type":act_type,"url":act_url,"date":0}, act_id)
					
					if act_type == "vod":
						dbsave("vod", {"id":act_id,"name":act_name,"playlist":fromVodID(s, act_id),"download":0}, act_id)
				
def report_parse(s, id):
	url = "http://etl.snu.ac.kr/report/ubcompletion/user_progress.php?id=" + str(id)
	req_report = s.get(url)
	bs = bs4.BeautifulSoup
	report_soup = bs(req_report.text, 'lxml')
	table_row = report_soup.find("table", class_="user_progress")
	if table_row == None:
		return 0
	table_row = table_row.find("tbody").find_all("tr")
	for row in table_row:
		col = row.find_all("td")
		i = 0
		if col[0].find("div") != None:
			week = col[i].find("div").contents[0]
			i += 1
		title = col[i].contents[-1]
		length = col[i+1].contents[0]
		time = col[i+2].contents
		if time:
			time = time[0]
		else:
			time = '0'
		percent = col[i+3].contents
		if percent:
			percent = percent[0]
		else:
			percent = '0'
		if title != " ":
			print(week, title,  length, time, percent)

def parse_date(date_str):
	start_str = date_str.split(' ~ ')[0]
	due_str = date_str.split(' ~ ')[1]
	# due_str 2022-04-04 10:00:00
	date = due_str.split(" ")[0]
	date_y, date_m, date_d = date.split("-")
	time = due_str.split(" ")[1]
	time_h , time_m, time_s = time.split(":")
	print(date_y, date_m, date_d, time_h, time_m, time_s)

def fromVodID(s, id: str):
	vodHtml = s.get("https://etl.snu.ac.kr/mod/vod/viewer.php?id="+id).text
	m3u8URL = vodHtml.split("[{file: ")[1].split("}")[0].replace("'", "")
	print(m3u8URL)
	return m3u8URL

def dbsave(db, data, ifnotexists):
	con = sqlite3.connect("./etl.db")
	cursor = con.cursor()
	query_data = "(" + ', '.join(data.keys()) + ") values ("
	for key in data.keys():
		if isinstance(data[key], str):
			query_data += f"'{data[key]}'"
		if isinstance(data[key], int):
			query_data += str(data[key])
		query_data += ", "
	query_data = query_data[0:-2]
	query_data += ")"
	query = f"INSERT OR IGNORE INTO {db} {query_data}"
	print(query)
	#input()
	cursor.execute(query)
	con.commit()
	con.close()

def newTable(db):
	con = sqlite3.connect("./etl.db")
	cursor = con.cursor()
	cursor.execute("CREATE TABLE " + db)
	con.commit()
	con.close()

def main():
	s = requests.Session()
	etl_login(s)
	# fromVodID(s, "1910241")
	# newTable("activity(id int unique, name text, subject text, type text, url text, date bool)")
	# newTable("vod(id int unique, name text, playlist text, download bool)")
	# newTable("due(id int unique, start datetime, end datetime, did bool)")
	courses = etl_parse(s)
	for course in courses:
		print("-----------------------------------\n"+course['title']+"\n-----------------------------------")
		# report_parse(s, course["id"])
		activity_parse(s, course['url'], course_title=course['title'])

main()

##################################################
# 
#  Database Table
#  
#  1 activity_id subject type url assign(0/1)
#  2 activity_id did?
#  3 activity_id download?
#
##################################################
