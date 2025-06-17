import re
import requests
import json
from bs4 import BeautifulSoup


class UISAuth:
    UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0"
    )

    url_login = "https://uis.fudan.edu.cn/authserver/login?service=https://fdjwgl.fudan.edu.cn/student/for-std/grade/sheet/"

    def __init__(self, uid, password):
        self.session = requests.session()
        self.session.keep_alive = False
        self.session.headers["User-Agent"] = self.UA
        self.uid = uid
        self.psw = password

    def _page_init(self):
        resp = self.session.get(self.url_login)
        resp.raise_for_status()
        return resp.text

    def login(self):
        html = self._page_init()
        # 提取登录表单隐藏字段
        hidden = dict(
            re.findall(
                r'<input type="hidden" name="([a-zA-Z0-9\-_]+)" value="([a-zA-Z0-9\-_]+)"/?>',
                html,
            )
        )
        data = {
            "username": self.uid,
            "password": self.psw,
            "service": "https://fdjwgl.fudan.edu.cn/student/for-std/grade/sheet/",
            **hidden,
        }

        headers = {
            "Host": "uis.fudan.edu.cn",
            "Origin": "https://uis.fudan.edu.cn",
            "Referer": self.url_login,
            "User-Agent": self.UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }

        resp = self.session.post(
            self.url_login, data=data, headers=headers, allow_redirects=False
        )
        if resp.status_code != 302:
            raise RuntimeError(
                "Login failed: unexpected status code {}".format(resp.status_code)
            )
        return resp

    def logout(self):
        exit_url = (
            "https://uis.fudan.edu.cn/authserver/logout?service=/authserver/login"
        )
        self.session.get(exit_url)

    def close(self):
        self.logout()
        self.session.close()


class FDJWGLClient:
    """
    用于登录 UIS，获取成绩表页面，提取 student id 并发起最终请求
    """

    SHEET_URL = "https://fdjwgl.fudan.edu.cn/student/for-std/grade/sheet/"
    FINAL_URL_TEMPLATE = (
        "https://fdjwgl.fudan.edu.cn/student/for-std/grade/sheet/info/{}?semester={}"
    )

    def __init__(self, uid, password):
        self.auth = UISAuth(uid, password)
        self.session = self.auth.session

    def close(self):
        """关闭会话并注销"""
        self.auth.close()

    def authenticate(self):
        """登录 UIS 并初始化会话"""
        resp = self.auth.login()
        # print("响应头部信息:", resp.headers)
        # self.cookies = resp.headers.get('Set-Cookie', '')

    def fetch_sheet(self):
        """请求成绩表页面并返回 HTML 文本"""

        # 执行跳转，获取包含 ticket 的跳转页（HTML 中含 JS）
        ticket_page = self.session.get(self.SHEET_URL, allow_redirects=True)
        if ticket_page.status_code != 200:
            raise RuntimeError("跳转失败，状态码: {}".format(ticket_page.status_code))

        # 用正则提取 ticket 或解析 form 中的 action
        match = re.search(r'locationValue\s*=\s*"([^"]+)"', ticket_page.text)
        if not match:
            raise RuntimeError("无法在跳转页中提取 ticket 路径")

        final_url = match.group(1).replace("&amp;", "&")  # HTML decode
        # print("最终跳转地址:", final_url)

        # 发起最终跳转
        final_landing = self.session.get(final_url, allow_redirects=True)
        print("最终响应状态:", final_landing.status_code)

        grade_page = self.session.get(
            "https://fdjwgl.fudan.edu.cn/student/for-std/grade/sheet",
            allow_redirects=True,
        )
        grade_page.raise_for_status()
        if grade_page.status_code != 200:
            raise RuntimeError(
                "获取成绩表页面失败，状态码: {}".format(grade_page.status_code)
            )
        # 返回最终页面的 HTML 内容
        return grade_page.text

    def extract_student_id(self, html):
        """使用正则从页面中匹配 student id"""
        # 假设页面中以 studentId=12345678 形式出现
        match = re.search(r'<input\s+id="studentId"[^>]*value="(\d+)"[^>]*>', html)
        if not match:
            raise ValueError("无法从页面中提取 student id")
        return match.group(1)
    
    def extract_text_fields(self, html_text):
        soup = BeautifulSoup(html_text, "html.parser")
        fields = [span.get_text(strip=True) for span in soup.find_all("span", class_="subGradeProcess")]
        return fields
    
    def fetch_final(self, student_id):
        """使用提取到的 student_id 构造最终请求并返回内容"""
        result = []
        
        # TODO
        semesters = [469, 467, 465, 464, 444, 425, 404, 426, 387, 385]

        for semester in semesters:
            url = self.FINAL_URL_TEMPLATE.format(student_id, semester)
            resp = self.session.get(url, allow_redirects=True)
            resp.raise_for_status()
            if resp.status_code == 200:
                print(f"成功获取学期 {semester} 的成绩数据")
                d = json.loads(resp.text)
                for item in d["semesterId2studentGrades"][str(semester)]:
                    item["gradeDetail"] = self.extract_text_fields(item["gradeDetail"])
                result.append(d)
            else:
                print(f"学期 {semester} 请求失败，状态码: {resp.status_code}")
        json.dump(
            result,
            open("grades.json", "w", encoding="utf-8"),
            ensure_ascii=False,
            indent=2,
        )

    def run(self):
        """完整执行流程：登录、获取页面、提取 ID、请求最终页面"""
        try:
            print("正在登录 UIS...")
            self.authenticate()
            print("登录成功，获取成绩表页面...")
            sheet_html = self.fetch_sheet()
            print("提取 student id...")
            sid = self.extract_student_id(sheet_html)
            print(f"找到 student id: {sid}")
            print("请求最终页面...")
            self.fetch_final(sid)
            print("最终成绩数据已保存到 grades.json")
        finally:
            self.auth.close()


if __name__ == "__main__":
    uis = ""
    pwd = ""
    if uis == "" or pwd == "":
        raise ValueError("请设置 UIS 用户名和密码")
    client = FDJWGLClient(uis, pwd)
    client.run()
    client.close()
