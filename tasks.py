import re
from workers import app
from downloader import send_request
from urllib import parse
from lxml import etree



@app.task(trail=True,ignore_result=True)
# trail=True 并行调用任务
# http://docs.jinkan.org/docs/celery/reference/celery.app.task.html
def crawl_pageurl_and_detailurl(url):
    response = send_request(url)
    if response:
        parse_page_data(response)

@app.task(trail=True,ignore_result=True)
def parse_page_data(response):
    """
    从旧网站中获取获取每一个分类的（政治、法律）关键字的搜索结果列表页中，提取论文详情的URL地址
    :param response:
    :return:
    """
    print('分页请求成功：'+ response.url)

    # 论文标题列表
    # 使用正则获取当前分类关键字和当前的页码数
    pattern = re.compile('.*?q=(.*?)\+.*?WF_(.*?)&.*?p=(\d+)', re.S)
    result = re.findall(pattern, response.url)[0]
    print(result)
    keyword = parse.unquote(result[0])
    tag = result[1]
    currentPage = result[2]
    etree_html = etree.HTML(response.text)
    # record-item-list
    itemList = etree_html.xpath('//div[@class="record-item-list"]/div[@class="record-item"]')
    print(tag+keyword+'第'+str(currentPage)+'页，'+'获取到了'+str(len(itemList))+'条数据。')
    if len(itemList) > 0:
        for item in itemList:
            itemTitle = ''.join(item.xpath('.//a[@class="title"]//text()')).replace(' ', '')
            itemUrl = item.xpath('.//a[@class="title"]/@href')[0]
            itemId = itemUrl.split('/')[-1:][0]
            if tag == 'HY':
                # 会议的详情
                # http://www.wanfangdata.com.cn/details/detail.do?_type=conference&id=7730508
                # print(itemTitle, itemUrl, '会议的详情',itemId)
                newItemUrl = 'http://www.wanfangdata.com.cn/details/detail.do?_type=conference&id=' + itemId
                info = {
                    'searchKeyWord': keyword,
                    'searchType': 'conference',
                    'title':itemTitle
                }

                app.send_task('tasks.crawl_detail_with_url',args=(newItemUrl,),kwargs=info)

            elif tag == "XW":
                # 学位的详情
                # http://www.wanfangdata.com.cn/details/detail.do?_type=degree&id=D01551993
                # print(itemTitle, itemUrl, '学位的详情',itemId)
                newItemUrl = 'http://www.wanfangdata.com.cn/details/detail.do?_type=degree&id=' + itemId
                info = {
                    'searchKeyWord': keyword,
                    'searchType': 'degree',
                    'title': itemTitle
                }
                app.send_task('tasks.crawl_detail_with_url', args=(newItemUrl,),kwargs=info)

            elif tag == "QK":
                # 期刊的详情
                # http://www.wanfangdata.com.cn/details/detail.do?_type=perio&id=bjgydxxb-shkx201902004
                # print(itemTitle, itemUrl, '期刊的详情', itemId)
                newItemUrl = 'http://www.wanfangdata.com.cn/details/detail.do?_type=perio&id=' + itemId
                info = {
                    'searchKeyWord': keyword,
                    'searchType': 'perio',
                    'title': itemTitle
                }

                app.send_task('tasks.crawl_detail_with_url', args=(newItemUrl,),kwargs=info)

    # 获取下一页
    nextUrls = etree_html.xpath('//p[@class="pager"]//a[@class="page"]/@href')

    # if len(nextUrls):
    #     for nextUrl in nextUrls:
    #         nextUrl = parse.urljoin(response.url,nextUrl)
    #         print(nextUrl)
    #         app.send_task('tasks.crawl_pageurl_and_detailurl',args=(nextUrl,))

@app.task(trail=True,ignore_result=True)
def crawl_detail_with_url(url,**kwargs):
    print('论文详情url地址:'+url)

    response = send_request(url)
    print('论文详情请求成功' + response.url)
    if response and url==response.url:
        title = kwargs['title']
        print('详情请求状态码', title, kwargs, response.status_code)
        app.send_task('tasks.parse_detail_data',args=(response.text,kwargs))

@app.task(trail=True)
def parse_detail_data(text,info):

    if info['searchType'] == 'degree':
        item = parse_degree(text, info)
        return item
    elif info['searchType'] == 'perio':
        item = parse_perio(text, info)
        return item
    elif info['searchType'] == 'conference':
        item = parse_conference(text, info)
        return item
    elif info['searchType'] == 'tech':
        item = parse_tech(text, info)
        return item

@app.task(trail=True)
def parse_degree(text, info):
    item = {}
    etree_html = etree.HTML(text)
    # item['url'] = response.url
    # title(中文标题)
    item['title'] = ''.join(etree_html.xpath('//div[@class="title"]/text()')).replace('\r\n', '').replace(
        '\t', '').replace('目录', '').replace(' ', '')

    # content(摘要)
    
    item['content'] = ''.join(etree_html.xpath('//div[@class="abstract"]/textarea/text()')).replace('\u3000','').replace('\t','').replace(' ', '').replace('\n','')

    # lis = etree_html.xpath('//ul[@class="info"]//li')
    # print(len(lis))
    # for li in lis:
    #     if li.xpath('./div[@class="info_left"]/text()')[0] == "关键词：":
    #         # keywords(关键词)
    #         item['keywords'] = '、'.join(li.xpath('.//a/text()'))
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "作者：":
    #         # authors(作者)
    #         item['authors'] = li.xpath('.//a[1]/text()')[0]
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "学位授予单位：":
    #         # 学位授权单位
    #         item['degreeUnit'] = li.xpath('.//a[1]/text()')[0]
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "授予学位：":
    #         # 授予学位
    #         item['awardedTheDegree'] = li.xpath('./div[@class="info_right author"]/text()')[0]
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "学科专业：":
    #         # 学科专业
    #         item['professional'] = li.xpath('.//a[1]/text()')[0]
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "导师姓名：":
    #         # 导师姓名
    #         item['mentorName'] = li.xpath('.//a[1]/text()')[0]
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "学位年度：":
    #         # 学位年度
    #         item['degreeInAnnual'] = li.xpath('./div[2]/text()')[0]
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "语种：":
    #         # 语种
    #         item['languages'] = li.xpath('./div[2]/text()')[0].replace('\r\n','').replace('\t', '')
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "分类号：":
    #         # 分类号
    #         item['classNumber'] = ' '.join(li.xpath('./div[2]//text()')[0]).replace('\r\n',' ').replace('\t', '').strip(' ')
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "在线出版日期：":
    #         # 在线出版日期
    #         item['publishTime'] = li.xpath('./div[2]/text()')[0].replace('\r\n', '').replace('\t', '').replace(' ', '')

    item['searchKey'] = info['searchKeyWord']
    item['searchType'] = info['searchType']

    return item

@app.task(trail=True)
def parse_perio(text, info):
    item = {}
    # item['url'] = response.url
    etree_html = etree.HTML(text)
    # title(中文标题)
    item['title'] = etree_html.xpath('//div[@class="title"]/text()')[0].replace('\r\n', '').replace(
        ' ', '').replace('\t', '')
    # englishTitle(英文标题)
    #item['englishTitle'] = etree_html.xpath('//div[@class="English"]/text()')[0].replace('\t', '')
    # content(摘要)
    item['content'] = ''.join(etree_html.xpath('//div[@class="abstract"]/textarea/text()')).replace('\u3000','').replace('\t','').replace(' ', '').replace('\n','')

    # lis = etree_html.xpath('//ul[@class="info"]//li')
    # print(len(lis))
    # for li in lis:
    #     # print(li.xpath('./div[@class="info_left"]/text()')[0])
    #     if li.xpath('./div[@class="info_left"]/text()')[0] == "doi：":
    #         item['doi'] = li.xpath('.//a/text()')[0].replace('\t', '').replace(' ', '')
    #     elif li.xpath('./div[@class="info_left "]/text()')[0] == "关键词：":
    #         # keywords(关键词)
    #         item['keywords'] = '、'.join(li.xpath('.//a/text()')[0])
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "Keyword：":
    #         item['englishKeyWords'] = '、'.join(li.xpath('.//a/text()')[0])
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "作者：":
    #         item['authors'] = '、'.join(li.xpath('./div[@class="info_right"]/a[@class="info_right_name"]/text()')[0])
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "Author：":
    #         item['englishAuthors'] = '、'.join(li.xpath('./div[@class="info_right"]/a[@class="info_right_name"]/text()')[0]).replace('\n', '')
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "作者单位：":
    #         item['unit'] = '、'.join(li.xpath('.//a/text()')[0])
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "刊名：":
    #         item['journalName'] = li.xpath('.//a[@class="college"]/text()')[0]
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "Journal：":
    #         item['journal'] = li.xpath('.//a[1]/text()')[0]
    #         if len(item['journal']) == 0:
    #             item['journal'] = li.xpath('.//div[2]/text()')[0].replace('\r\n', '').replace(' ',
    #                                                                                                          '').replace(
    #             '\t', '')
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "年，卷(期)：":
    #         item['yearsInfo'] = li.xpath('.//a/text()')[0]
    #         if len(item['yearsInfo']) == 0:
    #             item['yearsInfo'] = li.xpath('.//div[2]/text()')[0].replace('\r\n', '').replace(' ',
    #                                                                                                          '').replace(
    #             '\t', '')
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "所属期刊栏目：":
    #         item['journalSection'] = li.xpath('.//a/text()')[0]
    #         if len(item['journalSection']) == 0:
    #             item['journalSection'] = li.xpath('.//div[2]/text()')[0].replace('\r\n', '').replace(' ',
    #                                                                                                          '').replace(
    #             '\t', '')
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "分类号：":
    #         item['classNumber'] = li.xpath('.//div[2]/text()')[0].replace('\r', '').replace('\n',
    #                                                                                                        '').replace(
    #             '\t', '')
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "基金项目：":
    #         item['fundProgram'] = li.xpath('.//a[1]/text()')[0]
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "在线出版日期：":
    #         item['publishTime'] = li.xpath('.//div[2]/text()')[0].replace('\r\n', '').replace(' ',
    #                                                                                                          '').replace(
    #             '\t', '')
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "页数：":
    #         item['pages'] = li.xpath('.//div[2]/text()')[0].replace(' ','')
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "页码：":
    #         item['pageNumber'] = li.xpath('.//div[2]/text()')[0].replace(' ','')

    item['searchKey'] = info['searchKeyWord']
    item['searchType'] = info['searchType']
    return item

@app.task(trail=True)
def parse_conference(text, info):

    item = {}
    etree_html = etree.HTML(text)
    # item['url'] = response.url
    # title(中文标题)
    item['title'] = ''.join(etree_html.xpath('//div[@class="title"]/text()')).replace('\r\n', '').replace(
        '\t', '').replace('目录', '').replace(' ', '')
    # content(摘要)
    # item['content'] = ''.join(etree_html.xpath('//input[@class="share_summary"]/@value')[0]).replace('\t','').replace(' ', '').replace('\r\n', '').replace('\u3000', '')
    item['content'] = ''.join(etree_html.xpath('//div[@class="abstract"]/textarea/text()')).replace('\u3000','').replace('\t','').replace(' ', '').replace('\n','')

    lis = etree_html.xpath('//ul[@class="info"]//li')
    # print(len(lis))
    # for li in lis:
    #     if li.xpath('./div[@class="info_left"]/text()')[0] == "关键词：":
    #         # keywords(关键词)
    #         item['keywords'] = '、'.join(li.xpath('.//a/text()')[0])
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "作者：":
    #         # authors(作者)
    #         item['authors'] = '、'.join(li.xpath('.//a/text()')[0])
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "作者单位：":
    #         # 作者单位
    #         item['unit'] = '、'.join(li.xpath('.//a[1]/text()')[0])
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "母体文献：":
    #         # 母体文献
    #         item['literature'] = li.xpath('./div[2]/text()')[0]
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "会议名称：":
    #         # 会议名称
    #         item['meetingName'] = li.xpath('./div[2]/a[2]/text()')[0]
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "会议时间：":
    #         # 会议时间
    #         item['meetingTime'] = li.xpath('./div[2]/text()')[0].replace('\r\n', '').replace('\t',
    #                                                                                                         '').replace(
    #             ' ', '')
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "会议地点：":
    #         # 会议地点
    #         item['meetingAdress'] = li.xpath('./div[2]/text()')[0]
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "主办单位：":
    #         # 主办单位
    #         item['organizer'] = '、'.join(li.xpath('./div[2]//a/text()')[0])
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "语 种：":
    #         # 语种
    #         item['languages'] = li.xpath('./div[2]/text()')[0].replace('\r\n', '').replace('\t', '')
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "分类号：":
    #         # 分类号
    #         item['classNumber'] = ''.join(li.xpath('./div[2]/text()')).replace('\r\n', '').replace('\t',
    #                                                                                                          '')
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "在线出版日期：":
    #         # 发布时间
    #         item['publishTime'] = li.xpath('./div[2]/text()')[0].replace('\r\n', '').replace('\t',
    #                                                                                                         '').replace(
    #             ' ', '')
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "页码：":
    #         # 页码
    #         item['pageNumber'] = li.xpath('./div[2]/text()')[0]

    item['searchKey'] = info['searchKeyWord']
    item['searchType'] = info['searchType']
    return item

@app.task(trail=True)
def parse_tech(response, info):

    item = {}
    etree_html = etree.HTML(response.text)
    item['url'] = response.url
    # title(中文标题)
    item['title'] = etree_html.xpath('//div[@class="title"]/text()')[0].replace('\r\n', '').replace(
        ' ', '').replace('\t', '')
    # englishTitle(英文标题)
   # item['englishTitle'] = etree_html.xpath('//div[@class="English"]/text()')[0].replace('\t', '')
    # content(摘要)
    # item['content'] = ''.join(etree_html.xpath('//input[@class="share_summary"]/@value')[0]).replace('\t',
    #                                                                                                       '').replace(
    #     ' ', '').replace('\r\n', '')
    item['content'] = ''.join(etree_html.xpath('//div[@class="abstract"]/textarea/text()')).replace('\u3000','').replace('\t','').replace(' ', '').replace('\n','')

    # lis = etree_html.xpath('//ul[@class="info"]//li')
    # print(len(lis))
    # for li in lis:
    #     if li.xpath('./div[@class="info_left"]/text()')[0] == "关键词：":
    #         # keywords(关键词)
    #         item['keywords'] = '、'.join(li.xpath('.//a/text()')[0])
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "作者：":
    #         # authors(作者)
    #         item['authors'] = '、'.join(li.xpath('.//a/text()')[0])
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "作者单位：":
    #         # 作者单位
    #         item['unit'] = '、'.join(li.xpath('.//a[1]/text()')[0])
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "报告类型：":
    #         # 报告类型
    #         item['reportType'] = li.xpath('./div[2]/text()')[0]
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "公开范围：":
    #         # 公开范围
    #         item['openRange'] = li.xpath('./div[2]/text()')[0]
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "全文页数：":
    #         # 全文页数
    #         item['pageNumber'] = li.xpath('./div[2]/text()')[0]
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "项目/课题名称：":
    #         # 项目/课题名称
    #         item['projectName'] = li.xpath('./div[2]/text()')[0]
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "计划名称：":
    #         # 计划名称
    #         item['planName'] = li.xpath('./div[2]/text()')[0]
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "编制时间：":
    #         # 编制时间
    #         item['compileTime'] = li.xpath('./div[2]/text()')[0].replace('\t', '').replace(' ',
    #                                                                                                       '').replace(
    #             '\r\n', '')
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "立项批准年：":
    #         # 立项批准年
    #         item['approvalYear'] = li.xpath('./div[2]/text()')[0]
    #     elif li.xpath('./div[@class="info_left"]/text()')[0] == "馆藏号：":
    #         # 馆藏号
    #         item['collection'] = li.xpath('./div[2]/text()')[0]

    item['searchKey'] = info['searchKeyWord']
    item['searchType'] = info['searchType']
    return item



