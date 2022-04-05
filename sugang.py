from bs4 import BeautifulSoup as bs
import requests
import lxml
import json

def tpar(timeinfo):
	result = {'월':[],'화':[],'수':[],'목':[],'금':[],'토':[]}
	for each in timeinfo.split(" "):
		weekday = each[0]
		from_time = each[2:7]
		to_time = each[8:13]
		result[weekday].append({"from":from_time,"to":to_time})

	return result

def search(subject):
	searchUrl = "https://sugang.snu.ac.kr/sugang/cc/cc100InterfaceSrch.action"
	result = []
	if '1' in subject:
		subject_to = subject.replace('1', ' 1')
	else:
		subject_to = subject

	for page in range(1,20):
		searchPayload = {"workType": "S",
			"pageNo": str(page),
			"srchOpenSchyy": "2022",
			"srchOpenShtm": "U000200001U000300001",
			"srchSbjtNm": subject,
			"srchLanguage": "ko",
			"srchCurrPage": str(page),
			"srchPageSize": "9999"
		}
		searchReq = requests.post(searchUrl, data= searchPayload)
		searchHtml = searchReq.text

		searchSoup = bs(searchHtml, features="lxml")
		course = searchSoup.find_all("a", "course-info-detail")

		for course_info in course:
			name = course_info.find("div","course-name").find('strong').text.strip()
			if name == subject_to:
				course_info = course_info.find("ul","course-info").find_all('span')
				prof = course_info[0].text.strip()
				num = course_info[2].text.strip()
				time = course_info[6].text.strip()
				print({'name': name, 'prof': prof, 'info': num, 'time': time})
				#assert "." in num
				if ":" in time:
					time = tpar(time)

				result.append({'name': name, 'prof': prof, 'info': num, 'time': time})

			else:
				print(subject_to,"does not equals",name)
	return result

subs = ['대학영어1', '대학 글쓰기1', '수학1', '수학연습1', '물리학1', '물리학실험1', '통계학', '통계학실험']
for sub in subs:
	print(sub)
	with open('sugang.json', 'a', encoding='UTF-8') as f:
		result = search(sub)
		json.dump({sub: result, 'len': str(len(result))}, f, ensure_ascii=False)
		f.write("\n")
