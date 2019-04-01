from workers import app
#设置起始url任务（可以看作是scrapy-redis中的lpush）
from urllib.parse import quote
def set_start_url():
    #设置起始url的地址
    start_urls = []
    # 分类，根据分类和年限时间段添加url地址
    # QK：期刊 XW：学位 HY：会议
    categorys = ['QK','XW','HY',]
    # 关键字
    searchWords = ['法律','政治']
    for page in range(1, 5):
        # page 表示页码（例如：range(10, 100)：表示设置各分类的起始任务为10～100页，这里只需要给出一部分分页地址，在具体的代码中，会自动获取其他分页）
        # 注意：因为之前爬虫运行过了，redis数据库中保存着去重的指纹信息，设置的起始url可能之前爬取过了，所以起始url和截止url间区范围可以适当大一些
        for category in categorys:
            for searchWord in searchWords:
                #由这几个部分组成完整的url地址
                url = 'http://s.wanfangdata.com.cn/Paper.aspx?q=%s+DBID%sWF_%s&f=top&p=%s' % (quote(searchWord),'%3a',category,str(page))
                print(url)
                start_urls.append(url)
    return start_urls


def manage_crawl_task(urls):
    for url in urls:
        app.send_task('tasks.crawl_pageurl_and_detailurl', args=(url,))
if __name__ == '__main__':
    manage_crawl_task(set_start_url())