import requests

url="https://api5-normal-sinfonlineb.fqnovel.com/novel/commentapi/comment/list/7276384138653862966/v1?aid=1967&compliance_status=0&iid=4320438601941737&device_id=4320438601663209&ac=wifi&channel=fqxsfp_baidu_and_htl_2&app_name=novelapp&version_code=70932&version_name=7.0.9.32&device_platform=android&os=android&ssmix=a&device_type=ASUS_I005DA&device_brand=Asus&language=zh&os_api=28&os_version=9&manifest_version_code=70932&resolution=1600*1000&dpi=300&update_version_code=70932&_rticket=1773729138088&&host_abi=arm64-v8a&dragon_device_type=pad&pv_player=70932&need_personal_recommend=1&player_so_load=1&is_android_pad_screen=1&rom_version=Asus-user+9.0.0+20171130.276299+release-keys&cdid=e92d365f-9d84-43ba-a8ec-ff5c951d42e0"
res=requests.post(url, timeout=5)
