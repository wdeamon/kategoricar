import mechanize

class hzzoHtmlGetter():
	def __init__(self):
		self.url = "http://www.hzzo-net.hr/statos_MBO.htm"
	def getHtml(self, mbo):
		self.br = mechanize.Browser()
        	self.br.set_handle_robots(False)  # ignore robots
        	self.br.open(self.url, timeout=8.0)
        	self.br.select_form(name="isktr")
        	self.br["upmbo"] = mbo
        	self.br["answer"] = "11111"
        	self.res = self.br.submit()
        	self.br.close()
        	return self.res.read()
