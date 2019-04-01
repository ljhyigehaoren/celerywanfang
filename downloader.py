import requests
# 下载器封装简单封装部分
def send_request(url,callback=None,headers={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'},method='GET',params=None,data=None):
    if method=="GET" or params:
        response = requests.get(url,headers=headers,params=params)
        if response.status_code == 200:
            return response
        else:
            print(url,'请求失败')
            return None
    elif method == "POST" or data:
        requests.post()