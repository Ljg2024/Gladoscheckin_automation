import requests
import json
import os
import sys

from pypushdeer import PushDeer

# -------------------------------------------------------------------------------------------
# github workflows
# -------------------------------------------------------------------------------------------
if __name__ == '__main__':
    # pushdeer key 申请地址 https://www.pushdeer.com/product.html
    sckey = os.environ.get("SENDKEY", "")

    # 推送内容
    title = ""
    success, fail, repeats = 0, 0, 0        # 成功账号数量 失败账号数量 重复签到账号数量
    context = ""

    # glados账号cookie 直接使用数组 如果使用环境变量需要字符串分割一下
    cookies = os.environ.get("COOKIES", []).split("&")
    if cookies[0] != "":

        check_in_url = "https://glados.space/api/user/checkin"        # 签到地址
        status_url = "https://glados.space/api/user/status"          # 查看账户状态

        referer = 'https://glados.space/console/checkin'
        origin = "https://glados.space"
        useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
        payload = {
            'token': 'glados.one'
        }
        
        for cookie in cookies:
            cookie = cookie.strip()
            if not cookie:
                continue

            try:
                checkin = requests.post(
                    check_in_url,
                    headers={
                        'cookie': cookie,
                        'referer': referer,
                        'origin': origin,
                        'user-agent': useragent,
                        'content-type': 'application/json;charset=UTF-8'
                    },
                    data=json.dumps(payload),
                    timeout=20
                )
                state = requests.get(
                    status_url,
                    headers={
                        'cookie': cookie,
                        'referer': referer,
                        'origin': origin,
                        'user-agent': useragent
                    },
                    timeout=20
                )
            except requests.RequestException as exc:
                fail += 1
                context += f"账号: unknown, P: 0, 剩余: error | 请求异常: {exc} | "
                continue

            message_status = ""
            points = 0
            message_days = ""
            
            
            if checkin.status_code == 200:
                checkin_result = checkin.json()
                check_result = checkin_result.get('message', 'unknown')
                points = checkin_result.get('points', 0)
                check_code = checkin_result.get('code', -1)

                state_result = state.json() if state.status_code == 200 else {}
                state_data = state_result.get('data') or {}
                leftdays_raw = state_data.get('leftDays')
                email = state_data.get('email', 'unknown')
                
                print(check_result)
                if check_code == 0 and "Checkin! Got" in check_result:
                    success += 1
                    message_status = "签到成功，会员点数 + " + str(points)
                elif check_code == 0 and "Checkin Repeats!" in check_result:
                    repeats += 1
                    message_status = "重复签到，明天再来"
                else:
                    fail += 1
                    message_status = "签到失败: " + str(check_result)

                if leftdays_raw is not None:
                    message_days = f"{int(float(leftdays_raw))} 天"
                else:
                    message_days = "error"
            else:
                email = "unknown"
                message_status = "签到请求URL失败, 请检查..."
                message_days = "error"

            context += "账号: " + email + ", P: " + str(points) +", 剩余: " + message_days + " | "

        # 推送内容 
        title = f'Glados, 成功{success},失败{fail},重复{repeats}'
        print("Send Content:" + "\n", context)
        
    else:
        # 推送内容 
        title = f'# 未找到 cookies!'
        fail = 1

    # 推送消息
    #pushdeer = PushDeer(pushkey=sckey) 
    #pushdeer.send_text(title, desp=context)

    # 失败时让 GitHub Actions 标红，便于定位问题
    if fail > 0 and success == 0 and repeats == 0:
        sys.exit(1)
